from dataclasses import dataclass
from temporalio import activity
from temporalio.exceptions import ApplicationError
from ollama import chat, ChatResponse
import json


@dataclass
class ToolPromptInput:
    prompt: str
    context_instructions: str


class ToolActivities:
    @activity.defn
    def prompt_llm(self, input: ToolPromptInput) -> str:
        model_name = "qwen2.5:14b"
        messages = [
            {
                "role": "system",
                "content": input.context_instructions
                + ". The current date is "
                + get_current_date_human_readable(),
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


def get_current_date_human_readable():
    """
    Returns the current date in a human-readable format.

    Example: Wednesday, January 1, 2025
    """
    from datetime import datetime

    return datetime.now().strftime("%A, %B %d, %Y")
