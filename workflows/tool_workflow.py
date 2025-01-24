from collections import deque
from datetime import timedelta
from typing import Dict, Any, Union, List, Optional, Deque, TypedDict, Literal

from temporalio.common import RetryPolicy
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from activities.tool_activities import ToolActivities, ToolPromptInput
    from prompts.agent_prompt_generators import generate_genai_prompt
    from models.data_types import CombinedInput, ToolWorkflowParams

# Constants
MAX_TURNS_BEFORE_CONTINUE = 250
TOOL_ACTIVITY_TIMEOUT = timedelta(seconds=20)
LLM_ACTIVITY_TIMEOUT = timedelta(seconds=60)

# Type definitions
Message = Dict[str, Union[str, Dict[str, Any]]]
ConversationHistory = Dict[str, List[Message]]
NextStep = Literal["confirm", "question", "done"]


class ToolData(TypedDict, total=False):
    next: NextStep
    tool: str
    args: Dict[str, Any]
    response: str


@workflow.defn
class ToolWorkflow:
    """Workflow that manages tool execution with user confirmation and conversation history."""

    def __init__(self) -> None:
        self.conversation_history: ConversationHistory = {"messages": []}
        self.prompt_queue: Deque[str] = deque()
        self.conversation_summary: Optional[str] = None
        self.chat_ended: bool = False
        self.tool_data: Optional[ToolData] = None
        self.confirm: bool = False
        self.tool_results: List[Dict[str, Any]] = []

    async def _handle_tool_execution(
        self, current_tool: str, tool_data: ToolData
    ) -> None:
        """Execute a tool after confirmation and handle its result."""
        workflow.logger.info(f"Confirmed. Proceeding with tool: {current_tool}")

        dynamic_result = await workflow.execute_activity(
            current_tool,
            tool_data["args"],
            schedule_to_close_timeout=TOOL_ACTIVITY_TIMEOUT,
        )
        dynamic_result["tool"] = current_tool
        self.add_message(
            "tool_result", {"tool": current_tool, "result": dynamic_result}
        )

        self.prompt_queue.append(
            f"### The '{current_tool}' tool completed successfully with {dynamic_result}. "
            "INSTRUCTIONS: Parse this tool result as plain text, and use the system prompt containing the list of tools in sequence and the conversation history (and previous tool_results) to figure out next steps, if any. "
            '{"next": "<question|confirm|done>", "tool": "<tool_name or null>", "args": {"<arg1>": "<value1 or null>", "<arg2>": "<value2 or null>}, "response": "<plain text>"}'
            "ONLY return those json keys (next, tool, args, response), nothing else."
            'Next should only be "done" if all tools have been run (use the system prompt to figure that out).'
            'Next should be "question" if the tool is not the last one in the sequence.'
            'Next should NOT be "confirm" at this point.'
        )

    async def _handle_missing_args(
        self, current_tool: str, args: Dict[str, Any], tool_data: ToolData
    ) -> bool:
        """Check for missing arguments and handle them if found."""
        missing_args = [key for key, value in args.items() if value is None]

        if missing_args:
            self.prompt_queue.append(
                f"### INSTRUCTIONS set next='question', combine this response response='{tool_data.get('response')}' "
                f"and following missing arguments for tool {current_tool}: {missing_args}. "
                "Only provide a valid JSON response without any comments or metadata."
            )
            workflow.logger.info(
                f"Missing arguments for tool: {current_tool}: {' '.join(missing_args)}"
            )
            return True
        return False

    async def _continue_as_new_if_needed(self, agent_goal: Any) -> None:
        """Handle workflow continuation if message limit is reached."""
        if len(self.conversation_history["messages"]) >= MAX_TURNS_BEFORE_CONTINUE:
            summary_context, summary_prompt = self.prompt_summary_with_history()
            summary_input = ToolPromptInput(
                prompt=summary_prompt, context_instructions=summary_context
            )
            self.conversation_summary = await workflow.start_activity_method(
                ToolActivities.prompt_llm,
                summary_input,
                schedule_to_close_timeout=TOOL_ACTIVITY_TIMEOUT,
            )
            workflow.logger.info(
                f"Continuing as new after {MAX_TURNS_BEFORE_CONTINUE} turns."
            )
            workflow.continue_as_new(
                args=[
                    CombinedInput(
                        tool_params=ToolWorkflowParams(
                            conversation_summary=self.conversation_summary,
                            prompt_queue=self.prompt_queue,
                        ),
                        agent_goal=agent_goal,
                    )
                ]
            )

    @workflow.run
    async def run(self, combined_input: CombinedInput) -> str:
        """Main workflow execution method."""
        params = combined_input.tool_params
        agent_goal = combined_input.agent_goal

        if params and params.conversation_summary:
            self.add_message("conversation_summary", params.conversation_summary)
            self.conversation_summary = params.conversation_summary

        if params and params.prompt_queue:
            self.prompt_queue.extend(params.prompt_queue)

        waiting_for_confirm = False
        current_tool = None

        while True:
            await workflow.wait_condition(
                lambda: bool(self.prompt_queue) or self.chat_ended or self.confirm
            )

            if self.chat_ended:
                workflow.logger.info("Chat ended.")
                return f"{self.conversation_history}"

            if self.confirm and waiting_for_confirm and current_tool and self.tool_data:
                self.confirm = False
                waiting_for_confirm = False

                confirmed_tool_data = self.tool_data.copy()
                confirmed_tool_data["next"] = "user_confirmed_tool_run"
                self.add_message("user_confirmed_tool_run", confirmed_tool_data)

                await self._handle_tool_execution(current_tool, self.tool_data)
                continue

            if self.prompt_queue:
                prompt = self.prompt_queue.popleft()
                if not prompt.startswith("###"):
                    self.add_message("user", prompt)

                context_instructions = generate_genai_prompt(
                    agent_goal, self.conversation_history, self.tool_data
                )

                prompt_input = ToolPromptInput(
                    prompt=prompt,
                    context_instructions=context_instructions,
                )

                tool_data = await workflow.execute_activity(
                    ToolActivities.prompt_llm,
                    prompt_input,
                    schedule_to_close_timeout=LLM_ACTIVITY_TIMEOUT,
                    retry_policy=RetryPolicy(
                        maximum_attempts=5, initial_interval=timedelta(seconds=15)
                    ),
                )
                self.tool_data = tool_data

                next_step = tool_data.get("next")
                current_tool = tool_data.get("tool")

                if next_step == "confirm" and current_tool:
                    args = tool_data.get("args", {})
                    if await self._handle_missing_args(current_tool, args, tool_data):
                        continue

                    waiting_for_confirm = True
                    self.confirm = False
                    workflow.logger.info("Waiting for user confirm signal...")

                elif next_step == "done":
                    workflow.logger.info("All steps completed. Exiting workflow.")
                    self.add_message("agent", tool_data)
                    return str(self.conversation_history)

                self.add_message("agent", tool_data)
                await self._continue_as_new_if_needed(agent_goal)

    @workflow.signal
    async def user_prompt(self, prompt: str) -> None:
        """Signal handler for receiving user prompts."""
        if self.chat_ended:
            workflow.logger.warn(f"Message dropped due to chat closed: {prompt}")
            return
        self.prompt_queue.append(prompt)

    @workflow.signal
    async def end_chat(self) -> None:
        """Signal handler for ending the chat session."""
        self.chat_ended = True

    @workflow.signal
    async def confirm(self) -> None:
        """Signal handler for user confirmation of tool execution."""
        self.confirm = True

    @workflow.query
    def get_conversation_history(self) -> ConversationHistory:
        """Query handler to retrieve the full conversation history."""
        return self.conversation_history

    @workflow.query
    def get_summary_from_history(self) -> Optional[str]:
        """Query handler to retrieve the conversation summary if available."""
        return self.conversation_summary

    @workflow.query
    def get_tool_data(self) -> Optional[ToolData]:
        """Query handler to retrieve the current tool data if available."""
        return self.tool_data

    def format_history(self) -> str:
        """Format the conversation history into a single string."""
        return " ".join(
            str(msg["response"]) for msg in self.conversation_history["messages"]
        )

    def prompt_with_history(self, prompt: str) -> tuple[str, str]:
        """Generate a context-aware prompt with conversation history.

        Returns:
            tuple[str, str]: A tuple of (context_instructions, prompt)
        """
        history_string = self.format_history()
        context_instructions = (
            f"Here is the conversation history: {history_string} "
            "Please add a few sentence response in plain text sentences. "
            "Don't editorialize or add metadata. "
            "Keep the text a plain explanation based on the history."
        )
        return (context_instructions, prompt)

    def prompt_summary_with_history(self) -> tuple[str, str]:
        """Generate a prompt for summarizing the conversation.

        Returns:
            tuple[str, str]: A tuple of (context_instructions, prompt)
        """
        history_string = self.format_history()
        context_instructions = f"Here is the conversation history between a user and a chatbot: {history_string}"
        actual_prompt = (
            "Please produce a two sentence summary of this conversation. "
            'Put the summary in the format { "summary": "<plain text>" }'
        )
        return (context_instructions, actual_prompt)

    def add_message(self, actor: str, response: Union[str, Dict[str, Any]]) -> None:
        """Add a message to the conversation history.

        Args:
            actor: The entity that generated the message (e.g., "user", "agent")
            response: The message content, either as a string or structured data
        """
        self.conversation_history["messages"].append(
            {"actor": actor, "response": response}
        )
