from collections import deque
from datetime import timedelta
from typing import Deque, List, Optional, Tuple
from temporalio.common import RetryPolicy

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from activities.tool_activities import ToolActivities, ToolPromptInput
    from prompts.agent_prompt_generators import (
        generate_genai_prompt_from_tools_data,
    )
    from models.data_types import CombinedInput, ToolWorkflowParams


@workflow.defn
class ToolWorkflow:
    def __init__(self) -> None:
        self.conversation_history: List[Tuple[str, str]] = []
        self.prompt_queue: Deque[str] = deque()
        self.conversation_summary: Optional[str] = None
        self.chat_ended: bool = False
        self.tool_data = None
        self.max_turns_before_continue: int = 250

    @workflow.run
    async def run(self, combined_input: CombinedInput) -> str:

        params = combined_input.tool_params
        tools_data = combined_input.tools_data

        if params and params.conversation_summary:
            self.conversation_history.append(
                ("conversation_summary", params.conversation_summary)
            )
            self.conversation_summary = params.conversation_summary

        if params and params.prompt_queue:
            self.prompt_queue.extend(params.prompt_queue)

        while True:
            await workflow.wait_condition(
                lambda: bool(self.prompt_queue) or self.chat_ended
            )

            if self.prompt_queue:
                # 1) Get the user prompt -> call initial LLM
                prompt = self.prompt_queue.popleft()
                self.conversation_history.append(("user", prompt))
                context_instructions = generate_genai_prompt_from_tools_data(
                    tools_data, self.format_history()
                )
                prompt_input = ToolPromptInput(
                    prompt=prompt,
                    context_instructions=context_instructions,
                )
                responsePrechecked = await workflow.execute_activity_method(
                    ToolActivities.prompt_llm,
                    prompt_input,
                    schedule_to_close_timeout=timedelta(seconds=20),
                )

                # 2) Validate + parse in one shot
                tool_data = await workflow.execute_activity_method(
                    ToolActivities.validate_and_parse_json,
                    args=[responsePrechecked, tools_data, self.format_history()],
                    schedule_to_close_timeout=timedelta(seconds=40),
                    retry_policy=RetryPolicy(initial_interval=timedelta(seconds=10)),
                )

                # store it
                self.tool_data = tool_data
                self.conversation_history.append(("response", str(tool_data)))

                if self.tool_data.get("next") == "confirm":
                    dynamic_result = await workflow.execute_activity(
                        self.tool_data["tool"],  # dynamic activity name
                        self.tool_data["args"],  # single argument to pass
                        schedule_to_close_timeout=timedelta(seconds=20),
                    )

                    return dynamic_result

                # Continue as new after X turns
                if len(self.conversation_history) >= self.max_turns_before_continue:
                    # Summarize conversation
                    summary_context, summary_prompt = self.prompt_summary_with_history()
                    summary_input = ToolPromptInput(
                        prompt=summary_prompt,
                        context_instructions=summary_context,
                    )

                    self.conversation_summary = await workflow.start_activity_method(
                        ToolActivities.prompt_llm,
                        summary_input,
                        schedule_to_close_timeout=timedelta(seconds=20),
                    )

                    workflow.logger.info(
                        "Continuing as new after %i turns."
                        % self.max_turns_before_continue,
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

                continue

            # Handle end of chat
            if self.chat_ended:
                if len(self.conversation_history) > 1:
                    # Summarize conversation
                    summary_context, summary_prompt = self.prompt_summary_with_history()
                    summary_input = ToolPromptInput(
                        prompt=summary_prompt,
                        context_instructions=summary_context,
                    )

                    self.conversation_summary = await workflow.start_activity_method(
                        ToolActivities.prompt_llm,
                        summary_input,
                        schedule_to_close_timeout=timedelta(seconds=20),
                    )

                workflow.logger.info(
                    "Chat ended. Conversation summary:\n"
                    + f"{self.conversation_summary}"
                )
                return f"{self.conversation_history}"

    @workflow.signal
    async def user_prompt(self, prompt: str) -> None:
        if self.chat_ended:
            workflow.logger.warn(f"Message dropped due to chat closed: {prompt}")
            return
        self.prompt_queue.append(prompt)

    @workflow.signal
    async def end_chat(self) -> None:
        self.chat_ended = True

    @workflow.query
    def get_conversation_history(self) -> List[Tuple[str, str]]:
        return self.conversation_history

    @workflow.query
    def get_summary_from_history(self) -> Optional[str]:
        return self.conversation_summary

    @workflow.query
    def get_tool_data(self) -> Optional[str]:
        return self.tool_data

    # Helper: generate text of the entire conversation so far
    def format_history(self) -> str:
        return " ".join(f"{text}" for _, text in self.conversation_history)

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
        actual_prompt = "Please produce a two sentence summary of this conversation."
        return (context_instructions, actual_prompt)
