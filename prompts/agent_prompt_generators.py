import json
from typing import Optional

from models.tool_definitions import AgentGoal

MULTI_GOAL_MODE: bool = None


def generate_genai_prompt(
    agent_goal: AgentGoal,
    conversation_history: str,
    multi_goal_mode: bool,
    raw_json: Optional[str] = None,
    mcp_tools_info: Optional[dict] = None,
) -> str:
    """
    Generates a concise prompt for producing or validating JSON instructions
    with the provided tools and conversation history.
    """
    prompt_lines = []
    set_multi_goal_mode_if_unset(multi_goal_mode)

    # Intro / Role
    prompt_lines.append(
        "You are an AI agent that helps fill required arguments for the tools described below. "
        "You must respond with valid JSON ONLY, using the schema provided in the instructions."
    )

    # Main Conversation History
    prompt_lines.append("=== Conversation History ===")
    prompt_lines.append(
        "This is the ongoing history to determine which tool and arguments to gather:"
    )
    prompt_lines.append("*BEGIN CONVERSATION HISTORY*")
    prompt_lines.append(json.dumps(conversation_history, indent=2))
    prompt_lines.append("*END CONVERSATION HISTORY*")
    prompt_lines.append(
        "REMINDER: You can use the conversation history to infer arguments for the tools."
    )

    # Example Conversation History (from agent_goal)
    if agent_goal.example_conversation_history:
        prompt_lines.append("=== Example Conversation With These Tools ===")
        prompt_lines.append(
            "Use this example to understand how tools are invoked and arguments are gathered."
        )
        prompt_lines.append("BEGIN EXAMPLE")
        prompt_lines.append(agent_goal.example_conversation_history)
        prompt_lines.append("END EXAMPLE")
        prompt_lines.append("")

    # Add MCP server context if present
    if agent_goal.mcp_server_definition:
        prompt_lines.append("=== MCP Server Information ===")
        prompt_lines.append(
            f"Connected to MCP Server: {agent_goal.mcp_server_definition.name}"
        )
        if mcp_tools_info and mcp_tools_info.get("success", False):
            tools = mcp_tools_info.get("tools", {})
            server_name = mcp_tools_info.get("server_name", "Unknown")
            prompt_lines.append(
                f"MCP Tools loaded from {server_name} ({len(tools)} tools):"
            )
            for tool_name, tool_info in tools.items():
                prompt_lines.append(
                    f"  - {tool_name}: {tool_info.get('description', 'No description')}"
                )
        else:
            prompt_lines.append("Additional tools available via MCP integration:")
        prompt_lines.append("")

    # Tools Definitions
    prompt_lines.append("=== Tools Definitions ===")
    prompt_lines.append(f"There are {len(agent_goal.tools)} available tools:")
    prompt_lines.append(", ".join([t.name for t in agent_goal.tools]))
    prompt_lines.append(f"Goal: {agent_goal.description}")
    prompt_lines.append(
        "Gather the necessary information for each tool in the sequence described above."
    )
    prompt_lines.append(
        "Only ask for arguments listed below. Do not add extra arguments."
    )
    prompt_lines.append("")
    for tool in agent_goal.tools:
        prompt_lines.append(f"Tool name: {tool.name}")
        prompt_lines.append(f"  Description: {tool.description}")
        prompt_lines.append("  Required args:")
        for arg in tool.arguments:
            prompt_lines.append(f"    - {arg.name} ({arg.type}): {arg.description}")
        prompt_lines.append("")
    prompt_lines.append(
        "When all required args for a tool are known, you can propose next='confirm' to run it."
    )

    # JSON Format Instructions
    prompt_lines.append("=== Instructions for JSON Generation ===")
    prompt_lines.append(
        "Your JSON format must be:\n"
        "{\n"
        '  "response": "<plain text>",\n'
        '  "next": "<question|confirm|pick-new-goal|done>",\n'
        '  "tool": "<tool_name or null>",\n'
        '  "args": {\n'
        '    "<arg1>": "<value1 or null>",\n'
        '    "<arg2>": "<value2 or null>",\n'
        "    ...\n"
        "  }\n"
        "}"
    )
    prompt_lines.append(
        "1) If any required argument is missing, set next='question' and ask the user.\n"
        "2) If all required arguments are known, set next='confirm' and specify the tool.\n"
        "   The user will confirm before the tool is run.\n"
        f"3) {generate_toolchain_complete_guidance()}\n"
        "4) response should be short and user-friendly.\n\n"
        "Guardrails (always remember!)\n"
        "1) If any required argument is missing, set next='question' and ask the user.\n"
        "1) ALWAYS ask a question in your response if next='question'.\n"
        "2) ALWAYS set next='confirm' if you have arguments\n "
        'And respond with "let\'s proceed with <tool> (and any other useful info)" \n '
        + "DON'T set next='confirm' if you have a question to ask.\n"
        "EXAMPLE: If you have a question to ask, set next='question' and ask the user.\n"
        "3) You can carry over arguments from one tool to another.\n "
        "EXAMPLE: If you asked for an account ID, then use the conversation history to infer that argument "
        "going forward."
        "4) CRITICAL: Use sensible defaults for technical parameters instead of asking users. "
        "EXAMPLE: For list_products, use limit=100 instead of asking 'how many items would you like to see?'"
        "EXAMPLE: For browsing menus, show all relevant items rather than asking for technical limits."
        "5) CRITICAL: When users specify quantities (like '2 garlic breads'), be explicit in your response about the quantity. "
        "EXAMPLE: User says '2 garlic breads' -> response: 'Adding 2 Garlic Breads to your cart ($7.99 each).'"
        "EXAMPLE: Always confirm the exact quantity being added before proceeding with next='confirm'."
        "6) CRITICAL: If ListAgents in the conversation history is force_confirm='False', you MUST NOT ask permission "
        + "or include any questions in your response unless the current tool has userConfirmation defined. "
        + "NEVER say 'Is that okay?', 'Would you like me to...?', 'Should I...?', or any similar questions. "
        + "Instead, use confident declarative statements and set next='confirm' to execute immediately.\n"
        + "EXAMPLE: (force_confirm='False' AND no userConfirmation) -> response: 'Getting our menu items now.' next='confirm'\n"
        + "EXAMPLE: (force_confirm='False' AND no userConfirmation) -> response: 'Adding the pizza to your cart.' next='confirm'\n"
        + "EXAMPLE: (force_confirm='False' AND userConfirmation exists on tool) -> response: 'Would you like me to <run tool> "
        + "with the following details: <details>?' next='question'\n"
    )

    # Validation Task (If raw_json is provided)
    if raw_json is not None:
        prompt_lines.append("")
        prompt_lines.append("=== Validation Task ===")
        prompt_lines.append("Validate and correct the following JSON if needed:")
        prompt_lines.append(json.dumps(raw_json, indent=2))
        prompt_lines.append("")
        prompt_lines.append(
            "Check syntax, 'tool' validity, 'args' completeness, "
            "and set 'next' appropriately. Return ONLY corrected JSON."
        )

    # Prompt Start
    prompt_lines.append("")
    if raw_json is not None:
        prompt_lines.append("Begin by validating the provided JSON if necessary.")
    else:
        prompt_lines.append(
            "Begin by producing a valid JSON response for the next tool or question."
        )

    return "\n".join(prompt_lines)


def generate_tool_completion_prompt(current_tool: str, dynamic_result: dict) -> str:
    """
    Generates a prompt for handling tool completion and determining next steps.

    Args:
        current_tool: The name of the tool that just completed
        dynamic_result: The result data from the tool execution

    Returns:
        str: A formatted prompt string for the agent to process the tool completion
    """
    return (
        f"### The '{current_tool}' tool completed successfully with {dynamic_result}. "
        "INSTRUCTIONS: Parse this tool result as plain text, and use the system prompt containing the list of tools in sequence and the conversation history (and previous tool_results) to figure out next steps, if any. "
        "You will need to use the tool_results to auto-fill arguments for subsequent tools and also to figure out if all tools have been run. "
        '{"next": "<question|confirm|pick-new-goal|done>", "tool": "<tool_name or null>", "args": {"<arg1>": "<value1 or null>", "<arg2>": "<value2 or null>}, "response": "<plain text (can include \\n line breaks)>"}'
        "ONLY return those json keys (next, tool, args, response), nothing else. "
        'Next should be "question" if the tool is not the last one in the sequence. '
        'Next should be "done" if the user is asking to be done with the chat. '
        f"{generate_pick_new_goal_guidance()}"
    )


def generate_missing_args_prompt(
    current_tool: str, tool_data: dict, missing_args: list[str]
) -> str:
    """
    Generates a prompt for handling missing arguments for a tool.

    Args:
        current_tool: The name of the tool that needs arguments
        tool_data: The current tool data containing the response
        missing_args: List of argument names that are missing

    Returns:
        str: A formatted prompt string for requesting missing arguments
    """
    return (
        f"### INSTRUCTIONS set next='question', combine this response response='{tool_data.get('response')}' "
        f"and following missing arguments for tool {current_tool}: {missing_args}. "
        "Only provide a valid JSON response without any comments or metadata."
    )


def set_multi_goal_mode_if_unset(mode: bool) -> None:
    """
    Set multi-mode (used to pass workflow)

    Args:
        None

    Returns:
        bool: True if in multi-goal mode, false if not
    """
    global MULTI_GOAL_MODE
    if MULTI_GOAL_MODE is None:
        MULTI_GOAL_MODE = mode


def is_multi_goal_mode() -> bool:
    """
    Centralized logic for if we're in multi-goal mode.

    Args:
        None

    Returns:
        bool: True if in multi-goal mode, false if not
    """
    return MULTI_GOAL_MODE


def generate_pick_new_goal_guidance() -> str:
    """
    Generates a prompt for guiding the LLM to pick a new goal or be done depending on multi-goal mode.

    Args:
        None

    Returns:
        str: A prompt string prompting the LLM to when to go to pick-new-goal
    """
    if is_multi_goal_mode():
        return 'Next should only be "pick-new-goal" if all tools have been run for the current goal (use the system prompt to figure that out), or the user explicitly requested to pick a new goal.'
    else:
        return 'Next should never be "pick-new-goal".'


def generate_toolchain_complete_guidance() -> str:
    """
    Generates a prompt for guiding the LLM to handle the end of the toolchain.

    Args:
        None

    Returns:
        str: A prompt string prompting the LLM to prompt for a new goal, or be done
    """
    if is_multi_goal_mode():
        return "If no more tools are needed for the current goal (user_confirmed_tool_run has been run for all required tools), set next='pick-new-goal' and tool=null to allow the user to choose their next action."
    else:
        return "If no more tools are needed (user_confirmed_tool_run has been run for all), set next='done' and tool=null."
