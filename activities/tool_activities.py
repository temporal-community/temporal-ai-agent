from dataclasses import dataclass
from temporalio import activity
from ollama import chat, ChatResponse
from openai import OpenAI
import json
from typing import Sequence
from temporalio.common import RawValue
import os
from datetime import datetime


@dataclass
class ToolPromptInput:
    prompt: str
    context_instructions: str


class ToolActivities:
    @activity.defn
    def prompt_llm(self, input: ToolPromptInput) -> dict:
        client = OpenAI(
            api_key=os.environ.get(
                "OPENAI_API_KEY"
            ),  # This is the default and can be omitted
        )

        messages = [
            {
                "role": "system",
                "content": input.context_instructions
                + ". The current date is "
                + datetime.now().strftime("%B %d, %Y"),
            },
            {
                "role": "user",
                "content": input.prompt,
            },
        ]

        chat_completion = client.chat.completions.create(
            model="gpt-4o", messages=messages  # was gpt-4-0613
        )

        response_content = chat_completion.choices[0].message.content
        print(f"ChatGPT response: {response_content}")

        # Trim formatting markers if present
        if response_content.startswith("```json") and response_content.endswith("```"):
            response_content = response_content[7:-3].strip()

        try:
            data = json.loads(response_content)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            raise json.JSONDecodeError

        return data

    @activity.defn
    def prompt_llm_ollama(self, input: ToolPromptInput) -> dict:
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

        print(f"Chat response: {response.message.content}")

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
