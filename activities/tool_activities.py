from dataclasses import dataclass
from temporalio import activity
from temporalio.exceptions import ApplicationError
from ollama import chat, ChatResponse
import json
from typing import Sequence
from temporalio.common import RawValue


@dataclass
class ToolPromptInput:
    prompt: str
    context_instructions: str


class ToolActivities:
    @activity.defn
    def prompt_llm(self, input: ToolPromptInput) -> dict:
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

        try:
            data = json.loads(response.message.content)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            print(response.message.content)
            raise json.JSONDecodeError

        return data


def get_current_date_human_readable():
    """
    Returns the current date in a human-readable format.

    Example: Wednesday, January 1, 2025
    """
    from datetime import datetime

    return datetime.now().strftime("%A, %B %d, %Y")


@activity.defn(dynamic=True)
def dynamic_tool_activity(args: Sequence[RawValue]) -> dict:
    from tools import get_handler

    tool_name = activity.info().activity_type  # e.g. "FindEvents"
    tool_args = activity.payload_converter().from_payload(args[0].payload, dict)
    activity.logger.info(f"Running dynamic tool '{tool_name}' with args: {tool_args}")

    # Delegate to the relevant function
    handler = get_handler(tool_name)
    result = handler(tool_args)

    # Optionally log or augment the result
    activity.logger.info(f"Tool '{tool_name}' result: {result}")
    return result
