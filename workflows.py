from collections import deque
from dataclasses import dataclass
from datetime import timedelta
from typing import Deque, List, Optional, Tuple

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    # Import the updated OllamaActivities and the new dataclass
    from activities import OllamaActivities, OllamaPromptInput


@dataclass
class OllamaParams:
    conversation_summary: Optional[str] = None
    prompt_queue: Optional[Deque[str]] = None


@workflow.defn
class EntityOllamaWorkflow:
    def __init__(self) -> None:
        self.conversation_history: List[Tuple[str, str]] = []
        self.prompt_queue: Deque[str] = deque()
        self.conversation_summary: Optional[str] = None
        self.continue_as_new_per_turns: int = 6
        self.chat_ended: bool = False

    @workflow.run
    async def run(self, params: OllamaParams) -> str:
        if params and params.conversation_summary:
            self.conversation_history.append(
                ("conversation_summary", params.conversation_summary)
            )
            self.conversation_summary = params.conversation_summary

        if params and params.prompt_queue:
            self.prompt_queue.extend(params.prompt_queue)

        while True:
            workflow.logger.info("Waiting for prompts...")

            await workflow.wait_condition(
                lambda: bool(self.prompt_queue) or self.chat_ended
            )

            if self.prompt_queue:
                # Get user's prompt
                prompt = self.prompt_queue.popleft()
                self.conversation_history.append(("user", prompt))

                # Build prompt + context
                context_instructions, actual_prompt = self.prompt_with_history(prompt)
                workflow.logger.info("Prompt: " + prompt)

                # Pass a single input object
                prompt_input = OllamaPromptInput(
                    prompt=actual_prompt,
                    context_instructions=context_instructions,
                )

                # Call activity with one argument
                response = await workflow.execute_activity_method(
                    OllamaActivities.prompt_ollama,
                    prompt_input,
                    schedule_to_close_timeout=timedelta(seconds=20),
                )

                workflow.logger.info(f"Ollama response: {response}")
                self.conversation_history.append(("response", response))

                # Continue as new after X turns
                if len(self.conversation_history) >= self.continue_as_new_per_turns:
                    # Summarize conversation
                    summary_context, summary_prompt = self.prompt_summary_with_history()
                    summary_input = OllamaPromptInput(
                        prompt=summary_prompt,
                        context_instructions=summary_context,
                    )

                    self.conversation_summary = await workflow.start_activity_method(
                        OllamaActivities.prompt_ollama,
                        summary_input,
                        schedule_to_close_timeout=timedelta(seconds=20),
                    )

                    workflow.logger.info(
                        "Continuing as new after %i turns."
                        % self.continue_as_new_per_turns,
                    )

                    workflow.continue_as_new(
                        args=[
                            OllamaParams(
                                conversation_summary=self.conversation_summary,
                                prompt_queue=self.prompt_queue,
                            )
                        ]
                    )

                continue

            # Handle end of chat
            if self.chat_ended:
                if len(self.conversation_history) > 1:
                    # Summarize conversation
                    summary_context, summary_prompt = self.prompt_summary_with_history()
                    summary_input = OllamaPromptInput(
                        prompt=summary_prompt,
                        context_instructions=summary_context,
                    )

                    self.conversation_summary = await workflow.start_activity_method(
                        OllamaActivities.prompt_ollama,
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
        context_instructions = (
            f"Here is the conversation history between a user and a chatbot: {history_string}"
        )
        actual_prompt = (
            "Please produce a two sentence summary of this conversation."
        )
        return (context_instructions, actual_prompt)
