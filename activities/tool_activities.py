from dataclasses import dataclass
from temporalio import activity
from ollama import chat, ChatResponse
from openai import OpenAI
import json
from typing import Sequence
from temporalio.common import RawValue
import os
from datetime import datetime
import google.generativeai as genai


@dataclass
class ToolPromptInput:
    prompt: str
    context_instructions: str


class ToolActivities:
    @activity.defn
    def prompt_llm(self, input: ToolPromptInput) -> dict:
        llm_provider = os.environ.get("LLM_PROVIDER", "openai").lower()

        if llm_provider == "ollama":
            return self.prompt_llm_ollama(input)
        elif llm_provider == "google":
            return self.prompt_llm_google(input)
        else:
            return self.prompt_llm_openai(input)

    def prompt_llm_openai(self, input: ToolPromptInput) -> dict:
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

        # Use the new sanitize function
        response_content = self.sanitize_json_response(response_content)

        try:
            data = json.loads(response_content)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            raise json.JSONDecodeError

        return data

    @activity.defn
    def prompt_llm_ollama(self, input: ToolPromptInput) -> dict:
        model_name = os.environ.get("OLLAMA_MODEL_NAME", "qwen2.5:14b")
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

        # Use the new sanitize function
        response_content = self.sanitize_json_response(response.message.content)

        try:
            data = json.loads(response_content)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            print(response.message.content)
            raise json.JSONDecodeError

        return data

    def prompt_llm_google(self, input: ToolPromptInput) -> dict:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set in the environment variables.")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            "models/gemini-2.0-flash-exp",
            system_instruction=input.context_instructions,
        )
        response = model.generate_content(input.prompt)
        response_content = response.text
        print(f"Google Gemini response: {response_content}")

        # Use the new sanitize function
        response_content = self.sanitize_json_response(response_content)

        try:
            data = json.loads(response_content)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            raise json.JSONDecodeError

        return data

    def sanitize_json_response(self, response_content: str) -> str:
        """
        Extracts the JSON block from the response content as a string.
        Supports:
        - JSON surrounded by ```json and ```
        - Raw JSON input
        - JSON preceded or followed by extra text
        Rejects invalid input that doesn't contain JSON.
        """
        try:
            start_marker = "```json"
            end_marker = "```"

            json_str = None

            # Case 1: JSON surrounded by markers
            if start_marker in response_content and end_marker in response_content:
                json_start = response_content.index(start_marker) + len(start_marker)
                json_end = response_content.index(end_marker, json_start)
                json_str = response_content[json_start:json_end].strip()

            # Case 2: Text with valid JSON
            else:
                # Try to locate the JSON block by scanning for the first `{` and last `}`
                json_start = response_content.find("{")
                json_end = response_content.rfind("}")

                if json_start != -1 and json_end != -1 and json_start < json_end:
                    json_str = response_content[json_start : json_end + 1].strip()

            # Validate and ensure the extracted JSON is valid
            if json_str:
                json.loads(json_str)  # This will raise an error if the JSON is invalid
                return json_str

            # If no valid JSON found, raise an error
            raise ValueError("Response does not contain valid JSON.")

        except json.JSONDecodeError:
            # Invalid JSON
            print(f"Invalid JSON detected in response: {response_content}")
            raise ValueError("Response does not contain valid JSON.")
        except Exception as e:
            # Other errors
            print(f"Error processing response: {str(e)}")
            print(f"Full response: {response_content}")
            raise


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
