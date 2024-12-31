from collections import deque
from dataclasses import dataclass
from datetime import timedelta
from typing import Deque, List, Optional, Tuple

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from activities import OllamaActivities


@dataclass
class OllamaParams:
    conversation_summary: Optional[str] = None
    prompt_queue: Optional[Deque[str]] = None


@workflow.defn
class EntityOllamaWorkflow:
    def __init__(self) -> None:
        # List to store prompt history
        self.conversation_history: List[Tuple[str, str]] = []
        self.prompt_queue: Deque[str] = deque()
        self.conversation_summary: Optional[str] = None
        self.continue_as_new_per_turns: int = 6
        self.chat_ended: bool = False

    @workflow.run
    async def run(
        self,
        params: OllamaParams,
    ) -> str:

        if params and params.conversation_summary:
            self.conversation_history.append(
                ("conversation_summary", params.conversation_summary)
            )

            self.conversation_summary = params.conversation_summary

        if params and params.prompt_queue:
            self.prompt_queue.extend(params.prompt_queue)

        while True:
            workflow.logger.info("Waiting for prompts...")

            # Wait for a chat message (signal) or timeout
            await workflow.wait_condition(
                lambda: bool(self.prompt_queue) or self.chat_ended
            )

            if self.prompt_queue:
                # Fetch next user prompt and add to conversation history
                prompt = self.prompt_queue.popleft()
                self.conversation_history.append(("user", prompt))

                workflow.logger.info("Prompt: " + prompt)

                # Send prompt to Ollama
                response = await workflow.execute_activity_method(
                    OllamaActivities.prompt_ollama,
                    self.prompt_with_history(prompt),
                    schedule_to_close_timeout=timedelta(seconds=20),
                )

                workflow.logger.info(f"{response}")

                # Append the response to the conversation history
                self.conversation_history.append(("response", response))

                # Continue as new every x conversational turns to avoid event
                # history size getting too large. This is also to avoid the
                # prompt (with conversational history) getting too large for
                # AWS Ollama.

                # We summarize the chat to date and use that as input to the
                # new workflow
                if len(self.conversation_history) >= self.continue_as_new_per_turns:
                    # Summarize the conversation to date using Ollama
                    self.conversation_summary = await workflow.start_activity_method(
                        OllamaActivities.prompt_ollama,
                        self.prompt_summary_from_history(),
                        schedule_to_close_timeout=timedelta(seconds=20),
                    )

                    workflow.logger.info(
                        "Continuing as new due to %i conversational turns."
                        % self.continue_as_new_per_turns,
                    )

                    workflow.continue_as_new(
                        args=[
                            OllamaParams(
                                self.conversation_summary,
                                self.prompt_queue,
                            )
                        ]
                    )

                continue

            # If end chat signal was sent
            if self.chat_ended:
                # The workflow might be continued as new without any
                # chat to summarize, so only call Ollama if there
                # is more than the previous summary in the history.
                if len(self.conversation_history) > 1:
                    # Summarize the conversation to date using Ollama
                    self.conversation_summary = await workflow.start_activity_method(
                        OllamaActivities.prompt_ollama,
                        self.prompt_summary_from_history(),
                        schedule_to_close_timeout=timedelta(seconds=20),
                    )

                workflow.logger.info(
                    "Chat ended. Conversation summary:\n"
                    + f"{self.conversation_summary}"
                )

                return f"{self.conversation_history}"

    @workflow.signal
    async def user_prompt(self, prompt: str) -> None:
        # Chat ended but the workflow is waiting for a chat summary to be generated
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

    # Helper method used in prompts to Ollama
    def format_history(self) -> str:
        return " ".join(f"{text}" for _, text in self.conversation_history)

    # Create the prompt given to Ollama for each conversational turn
    def prompt_with_history(self, prompt: str) -> str:
        history_string = self.format_history()
        return (
            f"Here is the conversation history: {history_string} Please add "
            + "a few sentence response to the prompt in plain text sentences. "
            + "Don't editorialize or add metadata like response. Keep the "
            + f"text a plain explanation based on the history. Prompt: {prompt}"
        )

    # Create the prompt to Ollama to summarize the conversation history
    def prompt_summary_from_history(self) -> str:
        history_string = self.format_history()
        return (
            "Here is the conversation history between a user and a chatbot: "
            + f"{history_string}  -- Please produce a two sentence summary of "
            + "this conversation."
        )
