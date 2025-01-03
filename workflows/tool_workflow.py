from collections import deque
from datetime import timedelta
from typing import Dict, Any, Union, List, Optional, Deque
from temporalio.common import RetryPolicy

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from activities.tool_activities import ToolActivities, ToolPromptInput
    from prompts.agent_prompt_generators import (
        generate_genai_prompt,
    )
    from models.data_types import CombinedInput, ToolWorkflowParams


@workflow.defn
class ToolWorkflow:
    def __init__(self) -> None:
        self.conversation_history: Dict[
            str, List[Dict[str, Union[str, Dict[str, Any]]]]
        ] = {"messages": []}
        self.prompt_queue: Deque[str] = deque()
        self.conversation_summary: Optional[str] = None
        self.chat_ended: bool = False
        self.tool_data = None
        self.max_turns_before_continue: int = 250
        self.confirm = False
        self.tool_results: List[Dict[str, Any]] = []

    @workflow.run
    async def run(self, combined_input: CombinedInput) -> str:
        params = combined_input.tool_params
        tools_data = combined_input.tools_data
        tool_data = None

        if params and params.conversation_summary:
            self.add_message("conversation_summary", params.conversation_summary)
            self.conversation_summary = params.conversation_summary

        if params and params.prompt_queue:
            self.prompt_queue.extend(params.prompt_queue)

        waiting_for_confirm = False
        current_tool = None

        while True:
            # Wait until *any* signal or user prompt arrives:
            await workflow.wait_condition(
                lambda: bool(self.prompt_queue) or self.chat_ended or self.confirm
            )

            # 1) If chat_ended was signaled, handle end and return
            if self.chat_ended:

                workflow.logger.info("Chat ended.")
                return f"{self.conversation_history}"

            # 2) If we received a confirm signal:
            if self.confirm and waiting_for_confirm and current_tool:
                # Clear the confirm flag so we don't repeatedly confirm
                self.confirm = False
                waiting_for_confirm = False

                confirmed_tool_data = self.tool_data.copy()

                confirmed_tool_data["next"] = "confirmed"
                self.add_message("userToolConfirm", confirmed_tool_data)

                # Run the tool
                workflow.logger.info(f"Confirmed. Proceeding with tool: {current_tool}")
                dynamic_result = await workflow.execute_activity(
                    current_tool,
                    self.tool_data["args"],
                    schedule_to_close_timeout=timedelta(seconds=20),
                )
                dynamic_result["tool"] = current_tool
                self.add_message(
                    "tool_result", {"tool": current_tool, "result": dynamic_result}
                )

                # Enqueue a follow-up prompt for the LLM
                self.prompt_queue.append(
                    f"### The '{current_tool}' tool completed successfully with {dynamic_result}. "
                    "INSTRUCTIONS: Use this tool result, and the conversation history to figure out next steps. "
                    "IMPORTANT: If all listed tools have run, you are up to the final step. Mark 'next':'done' and respond with 'All tools run' or similar."
                )
                # Loop around again
                continue

            # 3) If there's a user prompt waiting, process it (unless we're in some other skipping logic).
            if self.prompt_queue:
                prompt = self.prompt_queue.popleft()
                if prompt.startswith("###"):
                    # this is a custom prompt where the tool result is sent to the LLM
                    self.add_message("tool_result_to_llm", prompt)
                else:
                    self.add_message("user", prompt)

                # Pass entire conversation + Tools to LLM
                context_instructions = generate_genai_prompt(
                    tools_data, self.format_history(), self.tool_data
                )
                prompt_input = ToolPromptInput(
                    prompt=prompt,
                    context_instructions=context_instructions,
                )
                tool_data = await workflow.execute_activity_method(
                    ToolActivities.prompt_llm,
                    prompt_input,
                    schedule_to_close_timeout=timedelta(seconds=60),
                    retry_policy=RetryPolicy(
                        maximum_attempts=5, initial_interval=timedelta(seconds=12)
                    ),
                )
                self.tool_data = tool_data
                self.add_message("response", tool_data)

                # Check the next step from LLM
                next_step = self.tool_data.get("next")
                current_tool = self.tool_data.get("tool")

                if next_step == "confirm" and current_tool:
                    waiting_for_confirm = True
                    self.confirm = False  # Clear any stale confirm
                    workflow.logger.info("Waiting for user confirm signal...")
                    # We do NOT do an immediate wait_condition here;
                    # instead, let the loop continue so we can still handle prompts/end_chat signals.

                elif next_step == "done":
                    workflow.logger.info("All steps completed. Exiting workflow.")
                    return str(self.conversation_history)

                # Possibly continue-as-new after many turns
                # todo ensure this doesn't lose critical context
                if (
                    len(self.conversation_history["messages"])
                    >= self.max_turns_before_continue
                ):
                    summary_context, summary_prompt = self.prompt_summary_with_history()
                    summary_input = ToolPromptInput(
                        prompt=summary_prompt, context_instructions=summary_context
                    )
                    self.conversation_summary = await workflow.start_activity_method(
                        ToolActivities.prompt_llm,
                        summary_input,
                        schedule_to_close_timeout=timedelta(seconds=20),
                    )
                    workflow.logger.info(
                        f"Continuing as new after {self.max_turns_before_continue} turns."
                    )
                    workflow.continue_as_new(
                        args=[
                            CombinedInput(
                                tool_params=ToolWorkflowParams(
                                    conversation_summary=self.conversation_summary,
                                    prompt_queue=self.prompt_queue,
                                ),
                                tools_data=tools_data,
                            )
                        ]
                    )

    @workflow.signal
    async def user_prompt(self, prompt: str) -> None:
        if self.chat_ended:
            workflow.logger.warn(f"Message dropped due to chat closed: {prompt}")
            return
        self.prompt_queue.append(prompt)

    @workflow.signal
    async def end_chat(self) -> None:
        self.chat_ended = True

    @workflow.signal
    async def confirm(self) -> None:
        self.confirm = True

    @workflow.query
    def get_conversation_history(
        self,
    ) -> Dict[str, List[Dict[str, Union[str, Dict[str, Any]]]]]:
        # Return the whole conversation as a dict
        return self.conversation_history

    @workflow.query
    def get_summary_from_history(self) -> Optional[dict]:
        return self.conversation_summary

    @workflow.query
    def get_tool_data(self) -> Optional[dict]:
        return self.tool_data

    # Helper: generate text of the entire conversation so far

    def format_history(self) -> str:
        return " ".join(
            str(msg["response"]) for msg in self.conversation_history["messages"]
        )

    # Return (context_instructions, prompt)
    def prompt_with_history(self, prompt: str) -> tuple[str, str]:
        history_string = self.format_history()
        context_instructions = (
            f"Here is the conversation history: {history_string} "
            "Please add a few sentence response in plain text sentences. "
            "Don't editorialize or add metadata. "
            "Keep the text a plain explanation based on the history."
        )
        return (context_instructions, prompt)

    # Return (context_instructions, prompt) for summarizing the conversation
    def prompt_summary_with_history(self) -> tuple[str, str]:
        history_string = self.format_history()
        context_instructions = f"Here is the conversation history between a user and a chatbot: {history_string}"
        actual_prompt = (
            "Please produce a two sentence summary of this conversation. "
            'Put the summary in the format { "summary": "<plain text>" }'
        )
        return (context_instructions, actual_prompt)

    def add_message(self, actor: str, response: Union[str, Dict[str, Any]]) -> None:
        # Append a message object to the "messages" list
        self.conversation_history["messages"].append(
            {"actor": actor, "response": response}
        )
