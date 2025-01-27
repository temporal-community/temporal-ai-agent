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
import anthropic
import deepseek
from dotenv import load_dotenv

load_dotenv(override=True)
print(
    "Using LLM: "
    + os.environ.get("LLM_PROVIDER")
    + " (set LLM_PROVIDER in .env to change)"
)

if os.environ.get("LLM_PROVIDER") == "ollama":
    print("Using Ollama (local) model: " + os.environ.get("OLLAMA_MODEL_NAME"))


@dataclass
class ToolPromptInput:
    prompt: str
    context_instructions: str


class ToolActivities:
    @activity.defn
    def prompt_llm(self, input: ToolPromptInput) -> dict:
        llm_provider = os.environ.get("LLM_PROVIDER", "openai").lower()

        print(f"LLM provider: {llm_provider}")

        if llm_provider == "ollama":
            return self.prompt_llm_ollama(input)
        elif llm_provider == "google":
            return self.prompt_llm_google(input)
        elif llm_provider == "anthropic":
            return self.prompt_llm_anthropic(input)
        elif llm_provider == "deepseek":
            return self.prompt_llm_deepseek(input)
        else:
            return self.prompt_llm_openai(input)

    def parse_json_response(self, response_content: str) -> dict:
        """
        Parses the JSON response content and returns it as a dictionary.
        """
        try:
            data = json.loads(response_content)
            return data
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            raise json.JSONDecodeError

    def prompt_llm_openai(self, input: ToolPromptInput) -> dict:
        client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
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

        return self.parse_json_response(response_content)

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

        return self.parse_json_response(response_content)

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

        return self.parse_json_response(response_content)

    def prompt_llm_anthropic(self, input: ToolPromptInput) -> dict:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set in the environment variables."
            )

        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=input.context_instructions,
            messages=[
                {
                    "role": "user",
                    "content": input.prompt,
                }
            ],
        )

        response_content = response.content[0].text
        print(f"Anthropic response: {response_content}")

        # Use the new sanitize function
        response_content = self.sanitize_json_response(response_content)

        return self.parse_json_response(response_content)

    def prompt_llm_deepseek(self, input: ToolPromptInput) -> dict:
        api_client = deepseek.DeepSeekAPI(api_key=os.environ.get("DEEPSEEK_API_KEY"))

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

        response = api_client.chat_completion(prompt=messages)
        response_content = response
        print(f"DeepSeek response: {response_content}")

        # Use the new sanitize function
        response_content = self.sanitize_json_response(response_content)

        return self.parse_json_response(response_content)

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
