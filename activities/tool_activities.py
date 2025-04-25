import inspect
from temporalio import activity
from ollama import chat, ChatResponse
from openai import OpenAI
import json
from typing import Sequence, Optional
from temporalio.common import RawValue
import os
from datetime import datetime
import google.generativeai as genai
import anthropic
import deepseek
from dotenv import load_dotenv
from models.data_types import EnvLookupOutput, ValidationInput, ValidationResult, ToolPromptInput, EnvLookupInput

load_dotenv(override=True)
print(
    "Using LLM provider: "
    + os.environ.get("LLM_PROVIDER", "openai")
    + " (set LLM_PROVIDER in .env to change)"
)

if os.environ.get("LLM_PROVIDER") == "ollama":
    print(
        "Using Ollama (local) model: "
        + os.environ.get("OLLAMA_MODEL_NAME", "qwen2.5:14b")
    )


class ToolActivities:
    def __init__(self):
        """Initialize LLM clients based on environment configuration."""
        self.llm_provider = os.environ.get("LLM_PROVIDER", "openai").lower()
        print(f"Initializing ToolActivities with LLM provider: {self.llm_provider}")

        # Initialize client variables (all set to None initially)
        self.openai_client: Optional[OpenAI] = None
        self.grok_client: Optional[OpenAI] = None
        self.anthropic_client: Optional[anthropic.Anthropic] = None
        self.genai_configured: bool = False
        self.deepseek_client: Optional[deepseek.DeepSeekAPI] = None
        self.ollama_model_name: Optional[str] = None
        self.ollama_initialized: bool = False

        # Only initialize the client specified by LLM_PROVIDER
        if self.llm_provider == "openai":
            if os.environ.get("OPENAI_API_KEY"):
                self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                print("Initialized OpenAI client")
            else:
                print("Warning: OPENAI_API_KEY not set but LLM_PROVIDER is 'openai'")
        
        elif self.llm_provider == "grok":
            if os.environ.get("GROK_API_KEY"):
                self.grok_client = OpenAI(api_key=os.environ.get("GROK_API_KEY"), base_url="https://api.x.ai/v1")
                print("Initialized grok client")
            else:
                print("Warning: GROK_API_KEY not set but LLM_PROVIDER is 'grok'")

        elif self.llm_provider == "anthropic":
            if os.environ.get("ANTHROPIC_API_KEY"):
                self.anthropic_client = anthropic.Anthropic(
                    api_key=os.environ.get("ANTHROPIC_API_KEY")
                )
                print("Initialized Anthropic client")
            else:
                print(
                    "Warning: ANTHROPIC_API_KEY not set but LLM_PROVIDER is 'anthropic'"
                )

        elif self.llm_provider == "google":
            api_key = os.environ.get("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.genai_configured = True
                print("Configured Google Generative AI")
            else:
                print("Warning: GOOGLE_API_KEY not set but LLM_PROVIDER is 'google'")

        elif self.llm_provider == "deepseek":
            if os.environ.get("DEEPSEEK_API_KEY"):
                self.deepseek_client = deepseek.DeepSeekAPI(
                    api_key=os.environ.get("DEEPSEEK_API_KEY")
                )
                print("Initialized DeepSeek client")
            else:
                print(
                    "Warning: DEEPSEEK_API_KEY not set but LLM_PROVIDER is 'deepseek'"
                )

        # For Ollama, we store the model name but actual initialization happens in warm_up_ollama
        elif self.llm_provider == "ollama":
            self.ollama_model_name = os.environ.get("OLLAMA_MODEL_NAME", "qwen2.5:14b")
            print(
                f"Using Ollama model: {self.ollama_model_name} (will be loaded on worker startup)"
            )
        else:
            print(
                f"Warning: Unknown LLM_PROVIDER '{self.llm_provider}', defaulting to OpenAI"
            )

    def warm_up_ollama(self):
        """Pre-load the Ollama model to avoid cold start latency on first request"""
        if self.llm_provider != "ollama" or self.ollama_initialized:
            return False  # No need to warm up if not using Ollama or already warmed up

        try:
            print(
                f"Pre-loading Ollama model '{self.ollama_model_name}' - this may take 30+ seconds..."
            )
            start_time = datetime.now()

            # Make a simple request to load the model into memory
            chat(
                model=self.ollama_model_name,
                messages=[
                    {"role": "system", "content": "You are an AI assistant"},
                    {
                        "role": "user",
                        "content": "Hello! This is a warm-up message to load the model.",
                    },
                ],
            )

            elapsed_time = (datetime.now() - start_time).total_seconds()
            print(f"✅ Ollama model loaded successfully in {elapsed_time:.2f} seconds")
            self.ollama_initialized = True
            return True
        except Exception as e:
            print(f"❌ Error pre-loading Ollama model: {str(e)}")
            print(
                "The worker will continue, but the first actual request may experience a delay."
            )
            return False

    @activity.defn
    async def agent_validatePrompt(
        self, validation_input: ValidationInput
    ) -> ValidationResult:
        """
        Validates the prompt in the context of the conversation history and agent goal.
        Returns a ValidationResult indicating if the prompt makes sense given the context.
        """
        # Create simple context string describing tools and goals
        tools_description = []
        for tool in validation_input.agent_goal.tools:
            tool_str = f"Tool: {tool.name}\n"
            tool_str += f"Description: {tool.description}\n"
            tool_str += "Arguments: " + ", ".join(
                [f"{arg.name} ({arg.type})" for arg in tool.arguments]
            )
            tools_description.append(tool_str)
        tools_str = "\n".join(tools_description)

        # Convert conversation history to string
        history_str = json.dumps(validation_input.conversation_history, indent=2)

        # Create context instructions
        context_instructions = f"""The agent goal and tools are as follows:
            Description: {validation_input.agent_goal.description}
            Available Tools:
            {tools_str}
            The conversation history to date is:
            {history_str}"""

        # Create validation prompt
        validation_prompt = f"""The user's prompt is: "{validation_input.prompt}"
            Please validate if this prompt makes sense given the agent goal and conversation history.
            If the prompt makes sense toward the goal then validationResult should be true.
            If the prompt is wildly nonsensical or makes no sense toward the goal and current conversation history then validationResult should be false.
            If the response is low content such as "yes" or "that's right" then the user is probably responding to a previous prompt.  
             Therefore examine it in the context of the conversation history to determine if it makes sense and return true if it makes sense.
            Return ONLY a JSON object with the following structure:
                "validationResult": true/false,
                "validationFailedReason": "If validationResult is false, provide a clear explanation to the user in the response field 
                about why their request doesn't make sense in the context and what information they should provide instead.
                validationFailedReason should contain JSON in the format
                {{
                    "next": "question",
                    "response": "[your reason here and a response to get the user back on track with the agent goal]"
                }}
                If validationResult is true (the prompt makes sense), return an empty dict as its value {{}}"
            """

        # Call the LLM with the validation prompt
        prompt_input = ToolPromptInput(
            prompt=validation_prompt, context_instructions=context_instructions
        )

        result = self.agent_toolPlanner(prompt_input)

        return ValidationResult(
            validationResult=result.get("validationResult", False),
            validationFailedReason=result.get("validationFailedReason", {}),
        )

    @activity.defn
    def agent_toolPlanner(self, input: ToolPromptInput) -> dict:
        if self.llm_provider == "ollama":
            return self.prompt_llm_ollama(input)
        elif self.llm_provider == "google":
            return self.prompt_llm_google(input)
        elif self.llm_provider == "anthropic":
            return self.prompt_llm_anthropic(input)
        elif self.llm_provider == "deepseek":
            return self.prompt_llm_deepseek(input)
        elif self.llm_provider == "grok":
            return self.prompt_llm_grok(input)
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
            raise

    def prompt_llm_openai(self, input: ToolPromptInput) -> dict:
        if not self.openai_client:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY is not set in the environment variables but LLM_PROVIDER is 'openai'"
                )
            self.openai_client = OpenAI(api_key=api_key)
            print("Initialized OpenAI client on demand")

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

        chat_completion = self.openai_client.chat.completions.create(
            model="gpt-4o", messages=messages  # was gpt-4-0613
        )

        response_content = chat_completion.choices[0].message.content
        activity.logger.info(f"ChatGPT response: {response_content}")

        # Use the new sanitize function
        response_content = self.sanitize_json_response(response_content)

        return self.parse_json_response(response_content)

    def prompt_llm_grok(self, input: ToolPromptInput) -> dict:
        if not self.grok_client:
            api_key = os.environ.get("GROK_API_KEY")
            if not api_key:
                raise ValueError(
                    "GROK_API_KEY is not set in the environment variables but LLM_PROVIDER is 'grok'"
                )
            self.grok_client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
            print("Initialized grok client on demand")

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

        chat_completion = self.grok_client.chat.completions.create(
            model="grok-2-1212", messages=messages  
        )

        response_content = chat_completion.choices[0].message.content
        activity.logger.info(f"Grok response: {response_content}")

        # Use the new sanitize function
        response_content = self.sanitize_json_response(response_content)

        return self.parse_json_response(response_content)
    def prompt_llm_ollama(self, input: ToolPromptInput) -> dict:
        # If not yet initialized, try to do so now (this is a backup if warm_up_ollama wasn't called or failed)
        if not self.ollama_initialized:
            print(
                "Ollama model not pre-loaded. Loading now (this may take 30+ seconds)..."
            )
            try:
                self.warm_up_ollama()
            except Exception:
                # We already logged the error in warm_up_ollama, continue with the actual request
                pass

        model_name = self.ollama_model_name or os.environ.get(
            "OLLAMA_MODEL_NAME", "qwen2.5:14b"
        )
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

        try:
            response: ChatResponse = chat(model=model_name, messages=messages)
            print(f"Chat response: {response.message.content}")

            # Use the new sanitize function
            response_content = self.sanitize_json_response(response.message.content)
            return self.parse_json_response(response_content)
        except (json.JSONDecodeError, ValueError) as e:
            # Re-raise JSON-related exceptions to let Temporal retry the activity
            print(f"JSON parsing error with Ollama response: {str(e)}")
            raise
        except Exception as e:
            # Log and raise other exceptions that may need retrying
            print(f"Error in Ollama chat: {str(e)}")
            raise

    def prompt_llm_google(self, input: ToolPromptInput) -> dict:
        if not self.genai_configured:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError(
                    "GOOGLE_API_KEY is not set in the environment variables but LLM_PROVIDER is 'google'"
                )
            genai.configure(api_key=api_key)
            self.genai_configured = True
            print("Configured Google Generative AI on demand")

        model = genai.GenerativeModel(
            "models/gemini-1.5-flash",
            system_instruction=input.context_instructions
            + ". The current date is "
            + datetime.now().strftime("%B %d, %Y"),
        )
        response = model.generate_content(input.prompt)
        response_content = response.text
        print(f"Google Gemini response: {response_content}")

        # Use the new sanitize function
        response_content = self.sanitize_json_response(response_content)

        return self.parse_json_response(response_content)

    def prompt_llm_anthropic(self, input: ToolPromptInput) -> dict:
        if not self.anthropic_client:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY is not set in the environment variables but LLM_PROVIDER is 'anthropic'"
                )
            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
            print("Initialized Anthropic client on demand")

        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",  
            #model="claude-3-7-sonnet-20250219",  # doesn't do as well
            max_tokens=1024,
            system=input.context_instructions
            + ". The current date is "
            + get_current_date_human_readable(),
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
        if not self.deepseek_client:
            api_key = os.environ.get("DEEPSEEK_API_KEY")
            if not api_key:
                raise ValueError(
                    "DEEPSEEK_API_KEY is not set in the environment variables but LLM_PROVIDER is 'deepseek'"
                )
            self.deepseek_client = deepseek.DeepSeekAPI(api_key=api_key)
            print("Initialized DeepSeek client on demand")

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

        response = self.deepseek_client.chat_completion(prompt=messages)
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

    # get env vars for workflow
    @activity.defn
    async def get_wf_env_vars(self, input: EnvLookupInput) -> EnvLookupOutput:
        """ gets env vars for workflow as an activity result so it's deterministic
            handles default/None
        """
        output: EnvLookupOutput = EnvLookupOutput(show_confirm=input.show_confirm_default, 
                                                  multi_goal_mode=True)
        show_confirm_value = os.getenv(input.show_confirm_env_var_name)
        if show_confirm_value is None:
            output.show_confirm = input.show_confirm_default
        elif show_confirm_value is not None and show_confirm_value.lower() == "false":
            output.show_confirm = False
        else:
            output.show_confirm = True
        
        first_goal_value = os.getenv("AGENT_GOAL")
        if first_goal_value is None:
            output.multi_goal_mode = True # default if unset
        elif first_goal_value is not None and first_goal_value.lower() != "goal_choose_agent_type":
            output.multi_goal_mode = False
        else:
            output.multi_goal_mode = True

        return output


def get_current_date_human_readable():
    """
    Returns the current date in a human-readable format.

    Example: Wednesday, January 1, 2025
    """
    from datetime import datetime

    return datetime.now().strftime("%A, %B %d, %Y")


@activity.defn(dynamic=True)
async def dynamic_tool_activity(args: Sequence[RawValue]) -> dict:
    from tools import get_handler

    tool_name = activity.info().activity_type  # e.g. "FindEvents"
    tool_args = activity.payload_converter().from_payload(args[0].payload, dict)
    activity.logger.info(f"Running dynamic tool '{tool_name}' with args: {tool_args}")

    # Delegate to the relevant function
    handler = get_handler(tool_name)
    if inspect.iscoroutinefunction(handler):
        result = await handler(tool_args)
    else:
        result = handler(tool_args)

    # Optionally log or augment the result
    activity.logger.info(f"Tool '{tool_name}' result: {result}")
    return result


