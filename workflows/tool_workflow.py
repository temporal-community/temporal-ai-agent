from collections import deque
from datetime import timedelta
from typing import Deque, List, Optional, Tuple
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
        tool_data = None

        if params and params.conversation_summary:
            self.conversation_history.append(
                ("conversation_summary", params.conversation_summary)
            )
            self.conversation_summary = params.conversation_summary

        if params and params.prompt_queue:
            self.prompt_queue.extend(params.prompt_queue)

        while True:
            # 1) Wait for a user prompt or an end-chat
            await workflow.wait_condition(
                lambda: bool(self.prompt_queue) or self.chat_ended
            )

            if self.chat_ended:
                # Possibly do a summary if multiple turns
                if len(self.conversation_history) > 1:
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

            # 2) Pop the user’s new message from the queue
            prompt = self.prompt_queue.popleft()
            self.conversation_history.append(("user", prompt))

            # 3) Call the LLM with the entire conversation + Tools
            context_instructions = generate_genai_prompt(
                tools_data, self.format_history(), tool_data
            )
            prompt_input = ToolPromptInput(
                prompt=prompt,
                context_instructions=context_instructions,
            )
            tool_data = await workflow.execute_activity_method(
                ToolActivities.prompt_llm,
                prompt_input,
                schedule_to_close_timeout=timedelta(seconds=20),
                retry_policy=RetryPolicy(
                    maximum_attempts=5, initial_interval=timedelta(seconds=15)
                ),
            )

            # 5) Store it and show the conversation
            self.tool_data = tool_data
            self.conversation_history.append(("response", str(tool_data)))

            # 6) Check for special flags
            next_step = self.tool_data.get("next")  # e.g. "confirm", "question", "done"
            current_tool = self.tool_data.get(
                "tool"
            )  # e.g. "FindEvents", "SearchFlights", "CreateInvoice"

            if next_step == "confirm" and current_tool:
                # We have enough info to call the tool
                dynamic_result = await workflow.execute_activity(
                    current_tool,
                    self.tool_data["args"],  # single argument
                    schedule_to_close_timeout=timedelta(seconds=20),
                )

                # Append tool’s result to the conversation
                self.conversation_history.append(
                    (f"{current_tool}_result", str(dynamic_result))
                )

                # Enqueue a follow-up question to the LLM
                self.prompt_queue.append(
                    f"The '{current_tool}' tool completed successfully with {dynamic_result}. "
                    "INSTRUCTIONS: Use this tool result, and the context_instructions (conversation history) to intelligently pre-fill the next tool's arguments. "
                    "What should we do next? "
                )
                # The loop continues, and on the next iteration, the workflow sees that new "prompt"
                # as if the user typed it, calls the LLM, etc.

            elif next_step == "done":
                # LLM signals no more tools needed
                workflow.logger.info("All steps completed. Exiting workflow.")
                return str(self.conversation_history)

            # 7) Optionally handle "continue_as_new" after many turns
            if len(self.conversation_history) >= self.max_turns_before_continue:
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

                # 8) If "next_step" is "question" or anything else,
                # we just keep looping, waiting for user prompt or signals.

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
                return f"{self.conversation_summary}"

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
