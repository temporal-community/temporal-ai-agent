import inspect
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from dotenv import load_dotenv
from litellm import completion
from temporalio import activity
from temporalio.common import RawValue
from temporalio.exceptions import ApplicationError

from models.data_types import (
    EnvLookupInput,
    EnvLookupOutput,
    ToolPromptInput,
    ValidationInput,
    ValidationResult,
)
from models.tool_definitions import MCPServerDefinition

# Import MCP client libraries
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    # Fallback if MCP not installed
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None

load_dotenv(override=True)


class ToolActivities:
    def __init__(self):
        """Initialize LLM client using LiteLLM."""
        self.llm_model = os.environ.get("LLM_MODEL", "openai/gpt-4")
        self.llm_key = os.environ.get("LLM_KEY")
        self.llm_base_url = os.environ.get("LLM_BASE_URL")
        print(f"Initializing ToolActivities with LLM model: {self.llm_model}")
        if self.llm_base_url:
            print(f"Using custom base URL: {self.llm_base_url}")

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

        result = await self.agent_toolPlanner(prompt_input)

        return ValidationResult(
            validationResult=result.get("validationResult", False),
            validationFailedReason=result.get("validationFailedReason", {}),
        )

    @activity.defn
    async def agent_toolPlanner(self, input: ToolPromptInput) -> dict:
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

        try:
            completion_kwargs = {
                "model": self.llm_model,
                "messages": messages,
                "api_key": self.llm_key,
            }

            # Add base_url if configured
            if self.llm_base_url:
                completion_kwargs["base_url"] = self.llm_base_url

            response = completion(**completion_kwargs)

            response_content = response.choices[0].message.content
            activity.logger.info(f"Raw LLM response: {repr(response_content)}")
            activity.logger.info(f"LLM response content: {response_content}")
            activity.logger.info(f"LLM response type: {type(response_content)}")
            activity.logger.info(
                f"LLM response length: {len(response_content) if response_content else 'None'}"
            )

            # Use the new sanitize function
            response_content = self.sanitize_json_response(response_content)
            activity.logger.info(f"Sanitized response: {repr(response_content)}")

            return self.parse_json_response(response_content)
        except Exception as e:
            print(f"Error in LLM completion: {str(e)}")
            raise

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

    def sanitize_json_response(self, response_content: str) -> str:
        """
        Sanitizes the response content to ensure it's valid JSON.
        """
        # Remove any markdown code block markers
        response_content = response_content.replace("```json", "").replace("```", "")

        # Remove any leading/trailing whitespace
        response_content = response_content.strip()

        return response_content

    @activity.defn
    async def get_wf_env_vars(self, input: EnvLookupInput) -> EnvLookupOutput:
        """gets env vars for workflow as an activity result so it's deterministic
        handles default/None
        """
        output: EnvLookupOutput = EnvLookupOutput(
            show_confirm=input.show_confirm_default, multi_goal_mode=False
        )
        show_confirm_value = os.getenv(input.show_confirm_env_var_name)
        if show_confirm_value is None:
            output.show_confirm = input.show_confirm_default
        elif show_confirm_value is not None and show_confirm_value.lower() == "false":
            output.show_confirm = False
        else:
            output.show_confirm = True

        first_goal_value = os.getenv("AGENT_GOAL")
        if first_goal_value is None:
            output.multi_goal_mode = False  # default to single agent mode if unset
        elif (
            first_goal_value is not None
            and first_goal_value.lower() == "goal_choose_agent_type"
        ):
            output.multi_goal_mode = True
        else:
            output.multi_goal_mode = False

        return output

    @activity.defn
    async def mcp_tool_activity(
        self, tool_name: str, tool_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """MCP Tool"""
        activity.logger.info(f"Executing MCP tool: {tool_name} with args: {tool_args}")

        # Extract server definition
        server_definition = tool_args.pop("server_definition", None)
        
        return await _execute_mcp_tool(tool_name, tool_args, server_definition)


@activity.defn(dynamic=True)
async def dynamic_tool_activity(args: Sequence[RawValue]) -> dict:
    from tools import get_handler

    tool_name = activity.info().activity_type  # e.g. "FindEvents"
    tool_args = activity.payload_converter().from_payload(args[0].payload, dict)
    activity.logger.info(f"Running dynamic tool '{tool_name}' with args: {tool_args}")

    # Check if this is an MCP tool call by looking for server_definition in args
    server_definition = tool_args.pop("server_definition", None)

    if server_definition:
        # This is an MCP tool call - handle it directly
        activity.logger.info(f"Executing MCP tool: {tool_name}")
        return await _execute_mcp_tool(tool_name, tool_args, server_definition)
    else:
        # This is a regular tool - delegate to the relevant function
        handler = get_handler(tool_name)
        if inspect.iscoroutinefunction(handler):
            result = await handler(tool_args)
        else:
            result = handler(tool_args)

        # Optionally log or augment the result
        activity.logger.info(f"Tool '{tool_name}' result: {result}")
        return result


# MCP Client Activities


def _build_connection(
    server_definition: MCPServerDefinition | Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Build connection parameters from MCPServerDefinition or dict"""
    if server_definition is None:
        # Default to stdio connection with the main server
        return {"type": "stdio", "command": "python", "args": ["server.py"], "env": {}}

    # Handle both MCPServerDefinition objects and dicts (from Temporal serialization)
    if isinstance(server_definition, dict):
        return {
            "type": server_definition.get("connection_type", "stdio"),
            "command": server_definition.get("command", "python"),
            "args": server_definition.get("args", ["server.py"]),
            "env": server_definition.get("env", {}) or {},
        }

    return {
        "type": server_definition.connection_type,
        "command": server_definition.command,
        "args": server_definition.args,
        "env": server_definition.env or {},
    }


def _normalize_result(result: Any) -> Any:
    """Normalize MCP tool result for serialization"""
    if hasattr(result, "content"):
        # Handle MCP result objects
        if hasattr(result.content, "__iter__") and not isinstance(result.content, str):
            return [
                item.text if hasattr(item, "text") else str(item)
                for item in result.content
            ]
        return str(result.content)
    return result


def _convert_args_types(tool_args: Dict[str, Any]) -> Dict[str, Any]:
    """Convert string arguments to appropriate types for MCP tools"""
    converted_args = {}

    for key, value in tool_args.items():
        if key == "server_definition":
            # Skip server_definition - it's metadata
            continue

        if isinstance(value, str):
            # Try to convert string values to appropriate types
            if value.isdigit():
                # Convert numeric strings to integers
                converted_args[key] = int(value)
            elif value.replace(".", "").isdigit() and value.count(".") == 1:
                # Convert decimal strings to floats
                converted_args[key] = float(value)
            elif value.lower() in ("true", "false"):
                # Convert boolean strings
                converted_args[key] = value.lower() == "true"
            else:
                # Keep as string
                converted_args[key] = value
        else:
            # Keep non-string values as-is
            converted_args[key] = value

    return converted_args


async def _execute_mcp_tool(
    tool_name: str, tool_args: Dict[str, Any], server_definition: MCPServerDefinition | Dict[str, Any] | None
) -> Dict[str, Any]:
    """Execute an MCP tool with the given arguments and server definition"""
    activity.logger.info(f"Executing MCP tool: {tool_name}")
    
    # Convert argument types for MCP tools
    converted_args = _convert_args_types(tool_args)
    connection = _build_connection(server_definition)

    try:
        if connection["type"] == "stdio":
            # Handle stdio connection
            async with _stdio_connection(
                command=connection.get("command", "python"),
                args=connection.get("args", ["server.py"]),
                env=connection.get("env", {}),
            ) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    activity.logger.info(
                        f"Initializing MCP session for {tool_name}"
                    )
                    await session.initialize()
                    activity.logger.info(f"MCP session initialized for {tool_name}")

                    # Call the tool
                    activity.logger.info(
                        f"Calling MCP tool {tool_name} with args: {converted_args}"
                    )
                    try:
                        result = await session.call_tool(
                            tool_name, arguments=converted_args
                        )
                        activity.logger.info(
                            f"MCP tool {tool_name} returned result: {result}"
                        )
                    except Exception as tool_exc:
                        activity.logger.error(
                            f"MCP tool {tool_name} call failed: {type(tool_exc).__name__}: {tool_exc}"
                        )
                        raise

                    normalized_result = _normalize_result(result)
                    activity.logger.info(
                        f"MCP tool {tool_name} completed successfully"
                    )

                    return {
                        "tool": tool_name,
                        "success": True,
                        "content": normalized_result,
                    }

        elif connection["type"] == "tcp":
            # Handle TCP connection (placeholder for future implementation)
            raise ApplicationError("TCP connections not yet implemented")

        else:
            raise ApplicationError(
                f"Unsupported connection type: {connection['type']}"
            )

    except Exception as e:
        activity.logger.error(f"MCP tool {tool_name} failed: {str(e)}")

        # Return error information
        return {
            "tool": tool_name,
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


@asynccontextmanager
async def _stdio_connection(command: str, args: list, env: dict):
    """Create stdio connection to MCP server"""
    if stdio_client is None:
        raise ApplicationError("MCP client libraries not available")

    # Create server parameters
    server_params = StdioServerParameters(command=command, args=args, env=env)

    async with stdio_client(server_params) as (read, write):
        yield read, write


@activity.defn
async def mcp_list_tools(
    server_definition: MCPServerDefinition, include_tools: Optional[List[str]] = None
) -> Dict[str, Any]:
    """List available MCP tools from the specified server"""

    activity.logger.info(f"Listing MCP tools for server: {server_definition.name}")

    connection = _build_connection(server_definition)

    try:
        if connection["type"] == "stdio":
            async with _stdio_connection(
                command=connection.get("command", "python"),
                args=connection.get("args", ["server.py"]),
                env=connection.get("env", {}),
            ) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    await session.initialize()

                    # List available tools
                    tools_response = await session.list_tools()

                    # Process tools based on include_tools filter
                    tools_info = {}
                    for tool in tools_response.tools:
                        # If include_tools is specified, only include those tools
                        if include_tools is None or tool.name in include_tools:
                            tools_info[tool.name] = {
                                "name": tool.name,
                                "description": tool.description,
                                "inputSchema": (
                                    tool.inputSchema.model_dump()
                                    if hasattr(tool.inputSchema, "model_dump")
                                    else str(tool.inputSchema)
                                ),
                            }

                    activity.logger.info(
                        f"Found {len(tools_info)} tools for server {server_definition.name}"
                    )

                    return {
                        "server_name": server_definition.name,
                        "success": True,
                        "tools": tools_info,
                        "total_available": len(tools_response.tools),
                        "filtered_count": len(tools_info),
                    }

        elif connection["type"] == "tcp":
            raise ApplicationError("TCP connections not yet implemented")

        else:
            raise ApplicationError(f"Unsupported connection type: {connection['type']}")

    except Exception as e:
        activity.logger.error(
            f"Failed to list tools for server {server_definition.name}: {str(e)}"
        )

        return {
            "server_name": server_definition.name,
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }
