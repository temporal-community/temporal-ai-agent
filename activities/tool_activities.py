from dataclasses import dataclass
from temporalio import activity
from temporalio.exceptions import ApplicationError
from ollama import chat, ChatResponse
import json
from models.tool_definitions import ToolsData
from typing import Sequence
from temporalio.common import RawValue


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

    @activity.defn
    def validate_and_parse_json(
        self,
        response_prechecked: str,
        tools_data: ToolsData,
        conversation_history: str,
    ) -> dict:
        """
        1) Build JSON validation instructions
        2) Call LLM with those instructions
        3) Parse the result
        4) If parsing fails, raise exception -> triggers retry
        """

        # 1) Build validation instructions
        #   (Generate the validation prompt exactly as you do in your workflow.)
        from prompts.agent_prompt_generators import (
            generate_json_validation_prompt_from_tools_data,
        )

        validation_prompt = generate_json_validation_prompt_from_tools_data(
            tools_data, conversation_history, response_prechecked
        )

        # 2) Call LLM
        prompt_input = ToolPromptInput(
            prompt=response_prechecked,
            context_instructions=validation_prompt,
        )
        validated_response = self.prompt_llm(prompt_input)

        # 3) Parse
        #    If parse fails, we raise ApplicationError -> triggers retry
        try:
            parsed = self.parse_tool_data(validated_response)
        except Exception as e:
            raise ApplicationError(f"Failed to parse validated JSON: {e}")

        # 4) If we get here, parse succeeded
        return parsed


def get_current_date_human_readable():
    """
    Returns the current date in a human-readable format.

    Example: Wednesday, January 1, 2025
    """
    from datetime import datetime

    return datetime.now().strftime("%A, %B %d, %Y")


@activity.defn(dynamic=True)
def dynamic_tool_activity(args: Sequence[RawValue]) -> dict:
    """Dynamic activity that is invoked via an unknown activity type."""
    tool_name = activity.info().activity_type  # e.g. "SearchFlights"

    # The first payload is the dictionary of arguments
    tool_args = activity.payload_converter().from_payload(args[0].payload, dict)

    # Extract fields from the arguments
    date_depart = tool_args.get("dateDepart")
    date_return = tool_args.get("dateReturn")
    origin = tool_args.get("origin")
    destination = tool_args.get("destination")

    # Print (or log) them
    activity.logger.info(f"Tool: {tool_name}")
    activity.logger.info(f"Depart: {date_depart}, Return: {date_return}")
    activity.logger.info(f"Origin: {origin}, Destination: {destination}")

    # For now, just return them
    return {
        "tool": tool_name,
        "args": tool_args,
        "status": "OK - dynamic activity stub",
    }
