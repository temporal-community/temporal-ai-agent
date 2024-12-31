from dataclasses import dataclass
from temporalio import activity
from ollama import chat, ChatResponse
import json
from temporalio.exceptions import ApplicationError


@dataclass
class OllamaPromptInput:
    prompt: str
    context_instructions: str


class OllamaActivities:
    @activity.defn
    def prompt_ollama(self, input: OllamaPromptInput) -> str:
        model_name = "qwen2.5:14b"
        messages = [
            {
                "role": "system",
                "content": input.context_instructions,
            },
            {
                "role": "user",
                "content": input.prompt,
            },
        ]

        response: ChatResponse = chat(model=model_name, messages=messages)
        return response.message.content

    @activity.defn
    def parse_tool_data(self, json_str: str) -> dict:
        """
        Parses a JSON string into a dictionary.
        Raises a ValueError if the JSON is invalid.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ApplicationError(f"Invalid JSON: {e}")

        return data
