from collections import deque
from datetime import timedelta
import os
from typing import Dict, Any, Union, List, Optional, Deque, TypedDict

from temporalio.common import RetryPolicy
from temporalio import workflow

from models.data_types import ConversationHistory, NextStep, ValidationInput
from models.tool_definitions import AgentGoal
from workflows.workflow_helpers import LLM_ACTIVITY_START_TO_CLOSE_TIMEOUT, \
    LLM_ACTIVITY_SCHEDULE_TO_CLOSE_TIMEOUT
from workflows import workflow_helpers as helpers

with workflow.unsafe.imports_passed_through():
    from activities.tool_activities import ToolActivities
    from prompts.agent_prompt_generators import (
        generate_genai_prompt
    )
    from models.data_types import (
        CombinedInput,
        ToolPromptInput,
    )
    from tools.goal_registry import goal_list

# Constants
MAX_TURNS_BEFORE_CONTINUE = 250

SHOW_CONFIRM = True
show_confirm_env = os.getenv("SHOW_CONFIRM")
if show_confirm_env is not None:
    if show_confirm_env == "False":
        SHOW_CONFIRM = False

#ToolData as part of the workflow is what's accessible to the UI - see LLMResponse.jsx for example
class ToolData(TypedDict, total=False):
    next: NextStep
    tool: str
    args: Dict[str, Any]
    response: str
    force_confirm: bool = True

@workflow.defn
class AgentGoalWorkflow:
    """Workflow that manages tool execution with user confirmation and conversation history."""

    def __init__(self) -> None:
        self.conversation_history: ConversationHistory = {"messages": []}
        self.prompt_queue: Deque[str] = deque()
        self.conversation_summary: Optional[str] = None
        self.chat_ended: bool = False
        self.tool_data: Optional[ToolData] = None
        self.confirm: bool = False
        self.tool_results: List[Dict[str, Any]] = []
        self.goal: AgentGoal = {"tools": []}

    # see ../api/main.py#temporal_client.start_workflow() for how the input parameters are set
    @workflow.run
    async def run(self, combined_input: CombinedInput) -> str:

        """Main workflow execution method."""
        # setup phase, starts with blank tool_params and agent_goal prompt as defined in tools/goal_registry.py
        params = combined_input.tool_params
        self.goal = combined_input.agent_goal

        # add message from sample conversation provided in tools/goal_registry.py, if it exists
        if params and params.conversation_summary:
            self.add_message("conversation_summary", params.conversation_summary)
            self.conversation_summary = params.conversation_summary

        if params and params.prompt_queue:
            self.prompt_queue.extend(params.prompt_queue)

        waiting_for_confirm = False 
        current_tool = None

        # This is the main interactive loop. Main responsibilities:
        #   - Selecting and changing goals as directed by the user
        #   - reacting to user input (from signals) 
        #   - validating user input to make sure it makes sense with the current goal and tools
        #   - calling the LLM through activities to determine next steps and prompts
        #   - executing the selected tools via activities
        while True:
            # wait indefinitely for input from signals - user_prompt, end_chat, or confirm as defined below
            await workflow.wait_condition(
                lambda: bool(self.prompt_queue) or self.chat_ended or self.confirm
            )

            # handle chat should end. When chat ends, push conversation history to workflow results.
            if self.chat_should_end():
                return f"{self.conversation_history}"

            # Execute the tool 
            if self.ready_for_tool_execution(waiting_for_confirm, current_tool):
                waiting_for_confirm = await self.execute_tool(current_tool)
                continue

            # process forward on the prompt queue if any
            if self.prompt_queue:
                # get most recent prompt
                prompt = self.prompt_queue.popleft()
                workflow.logger.info(f"workflow step: processing message on the prompt queue, message is {prompt}")
                
                # Validate user-provided prompts
                if self.is_user_prompt(prompt): 
                    self.add_message("user", prompt)

                    # Validate the prompt before proceeding
                    validation_input = ValidationInput(
                        prompt=prompt,
                        conversation_history=self.conversation_history,
                        agent_goal=self.goal,
                    )
                    validation_result = await workflow.execute_activity(
                        ToolActivities.agent_validatePrompt,
                        args=[validation_input],
                        schedule_to_close_timeout=LLM_ACTIVITY_SCHEDULE_TO_CLOSE_TIMEOUT,
                        start_to_close_timeout=LLM_ACTIVITY_START_TO_CLOSE_TIMEOUT,
                        retry_policy=RetryPolicy(
                            initial_interval=timedelta(seconds=5), backoff_coefficient=1
                        ),
                    )

                    # If validation fails, provide that feedback to the user - i.e., "your words make no sense, puny human" end this iteration of processing
                    if not validation_result.validationResult:
                        workflow.logger.warning(f"Prompt validation failed: {validation_result.validationFailedReason}")
                        self.add_message("agent", validation_result.validationFailedReason)
                        continue

                # If valid, proceed with generating the context and prompt
                context_instructions = generate_genai_prompt(self.goal, self.conversation_history, self.tool_data)
                prompt_input = ToolPromptInput(prompt=prompt, context_instructions=context_instructions)

                # connect to LLM and execute to get next steps
                tool_data = await workflow.execute_activity(
                    ToolActivities.agent_toolPlanner,
                    prompt_input,
                    schedule_to_close_timeout=LLM_ACTIVITY_SCHEDULE_TO_CLOSE_TIMEOUT,
                    start_to_close_timeout=LLM_ACTIVITY_START_TO_CLOSE_TIMEOUT,
                    retry_policy=RetryPolicy(
                        initial_interval=timedelta(seconds=5), backoff_coefficient=1
                    ),
                )
                tool_data["force_confirm"] = SHOW_CONFIRM
                self.tool_data = tool_data

                # process the tool as dictated by the prompt response - what to do next, and with which tool
                next_step = tool_data.get("next")
                current_tool = tool_data.get("tool")

                workflow.logger.info(f"next_step: {next_step}, current tool is {current_tool}")

                #if the next step is to confirm...
                if next_step == "confirm" and current_tool:
                    args = tool_data.get("args", {})
                    #if we're missing arguments, go back to the top of the loop
                    if await helpers.handle_missing_args(current_tool, args, tool_data, self.prompt_queue):
                        continue

                    #...otherwise, if we want to force the user to confirm, set that up
                    waiting_for_confirm = True
                    if SHOW_CONFIRM:
                        self.confirm = False
                        workflow.logger.info("Waiting for user confirm signal...")
                    else:
                        #theory - set self.confirm to true bc that's the signal, so we can get around the signal??
                        self.confirm = True

                # else if the next step is to pick a new goal...
                elif next_step == "pick-new-goal":
                    workflow.logger.info("All steps completed. Resetting goal.")
                    self.change_goal("goal_choose_agent_type")
                
                # else if the next step is to be done - this should only happen if the user requests it via "end conversation"
                elif next_step == "done":
                    self.add_message("agent", tool_data)
                    # end the workflow
                    return str(self.conversation_history)

                self.add_message("agent", tool_data)
                await helpers.continue_as_new_if_needed(
                    self.conversation_history,
                    self.prompt_queue,
                    self.goal,
                    MAX_TURNS_BEFORE_CONTINUE,
                    self.add_message
                )

    #Signal that comes from api/main.py via a post to /send-prompt
    @workflow.signal
    async def user_prompt(self, prompt: str) -> None:
        """Signal handler for receiving user prompts."""
        workflow.logger.info(f"signal received: user_prompt, prompt is {prompt}")
        if self.chat_ended:
            workflow.logger.info(f"Message dropped due to chat closed: {prompt}")
            return
        self.prompt_queue.append(prompt)

    #Signal that comes from api/main.py via a post to /confirm
    @workflow.signal
    async def confirm(self) -> None:
        """Signal handler for user confirmation of tool execution."""
        workflow.logger.info("Received user signal: confirmation")
        self.confirm = True

    #Signal that comes from api/main.py via a post to /end-chat
    @workflow.signal
    async def end_chat(self) -> None:
        """Signal handler for ending the chat session."""
        workflow.logger.info("signal received: end_chat")
        self.chat_ended = True

    @workflow.query
    def get_conversation_history(self) -> ConversationHistory:
        """Query handler to retrieve the full conversation history."""
        return self.conversation_history
    
    @workflow.query
    def get_agent_goal(self) -> AgentGoal:
        """Query handler to retrieve the current goal of the agent."""
        return self.goal

    @workflow.query
    def get_summary_from_history(self) -> Optional[str]:
        """Query handler to retrieve the conversation summary if available. 
        Used only for continue as new of the workflow."""
        return self.conversation_summary

    @workflow.query
    def get_latest_tool_data(self) -> Optional[ToolData]:
        """Query handler to retrieve the latest tool data response if available."""
        return self.tool_data

    def add_message(self, actor: str, response: Union[str, Dict[str, Any]]) -> None:
        """Add a message to the conversation history.

        Args:
            actor: The entity that generated the message (e.g., "user", "agent")
            response: The message content, either as a string or structured data
        """
        if isinstance(response, dict):
            response_str = str(response)
            workflow.logger.debug(f"Adding {actor} message: {response_str[:100]}...")
        else:
            workflow.logger.debug(f"Adding {actor} message: {response[:100]}...")

        self.conversation_history["messages"].append(
            {"actor": actor, "response": response}
        )

    def change_goal(self, goal: str) -> None:
        '''goalsLocal = {
            "goal_match_train_invoice": goal_match_train_invoice,
            "goal_event_flight_invoice": goal_event_flight_invoice,
            "goal_choose_agent_type": goal_choose_agent_type,
        }'''

        if goal is not None:
            for listed_goal in goal_list:
                if listed_goal.id == goal:
                    self.goal = listed_goal
        #    self.goal = goals.get(goal)
                    workflow.logger.info("Changed goal to " + goal)
        #todo reset goal or tools if this doesn't work or whatever

    # workflow function that defines if chat should end
    def chat_should_end(self) -> bool:
        if self.chat_ended:
            workflow.logger.info("Chat-end signal received. Chat ending.")
            return True
        else:
            return False
    
    # define if we're ready for tool execution
    def ready_for_tool_execution(self, waiting_for_confirm: bool, current_tool: Any) -> bool:
        if self.confirm and waiting_for_confirm and current_tool and self.tool_data:
            return True
        else:
            return False

    # LLM-tagged prompts start with "###"
    # all others are from the user
    def is_user_prompt(self, prompt) -> bool:
         if prompt.startswith("###"):
             return False
         else:
             return True
        
    # execute the tool - return False if we're not waiting for confirm anymore (always the case if it works successfully)
    # 
    async def execute_tool(self, current_tool: str)->bool:
        workflow.logger.info(f"workflow step: user has confirmed, executing the tool {current_tool}")
        self.confirm = False
        waiting_for_confirm = False
        confirmed_tool_data = self.tool_data.copy()
        confirmed_tool_data["next"] = "user_confirmed_tool_run"
        self.add_message("user_confirmed_tool_run", confirmed_tool_data)

        # execute the tool by key as defined in tools/__init__.py
        await helpers.handle_tool_execution(
            current_tool,
            self.tool_data,
            self.tool_results,
            self.add_message,
            self.prompt_queue
        )

        #set new goal if we should
        if len(self.tool_results) > 0:
            if "ChangeGoal" in self.tool_results[-1].values() and "new_goal" in self.tool_results[-1].keys():
                new_goal = self.tool_results[-1].get("new_goal")
                workflow.logger.info(f"Booya new goal!: {new_goal}")
                self.change_goal(new_goal)
            elif "ListAgents" in self.tool_results[-1].values() and self.goal.id != "goal_choose_agent_type":
                workflow.logger.info("setting goal to goal_choose_agent_type")
                self.change_goal("goal_choose_agent_type")
        return waiting_for_confirm
        

    
