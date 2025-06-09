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
        "CRITICAL: You must respond with ONLY valid JSON using the exact schema provided. "
        "DO NOT include any text before or after the JSON. Your entire response must be parseable JSON."
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
        "CRITICAL: You MUST follow the complete sequence described in the Goal above. "
        "Do NOT skip steps or assume the goal is complete until ALL steps are done."
    )
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
    prompt_lines.append("=== CRITICAL: JSON-ONLY RESPONSE FORMAT ===")
    prompt_lines.append(
        "MANDATORY: Your response must be ONLY valid JSON with NO additional text.\n"
        "NO explanations, NO comments, NO text before or after the JSON.\n"
        "Your entire response must start with '{' and end with '}'.\n\n"
        "Required JSON format:\n"
        "{\n"
        '  "response": "<plain text>",\n'
        '  "next": "<question|confirm|pick-new-goal|done>",\n'
        '  "tool": "<tool_name or null>",\n'
        '  "args": {\n'
        '    "<arg1>": "<value1 or null>",\n'
        '    "<arg2>": "<value2 or null>",\n'
        "    ...\n"
        "  }\n"
        "}\n\n"
        "INVALID EXAMPLE: 'Thank you for providing... {\"response\": ...}'\n"
        "VALID EXAMPLE: '{\"response\": \"Thank you for providing...\", \"next\": ...}'"
    )
    prompt_lines.append(
        "DECISION LOGIC (follow this exact order):\n"
        "1) Do I need to run a tool next?\n"
        "   - If your response says 'let's get/proceed/check/add/create/finalize...' -> YES, you need a tool\n"
        "   - If you're announcing what you're about to do -> YES, you need a tool\n"
        "   - If no more steps needed for current goal -> NO, go to step 3\n\n"
        "2) If YES to step 1: Do I have all required arguments?\n"
        "   - Check tool definition for required args\n"
        "   - Can I fill missing args from conversation history?\n"
        "   - Can I use sensible defaults (limit=100, etc.)?\n"
        "   - If ALL args available/inferrable -> set next='confirm', specify tool and args\n"
        "   - If missing required args -> set next='question', ask for missing args, tool=null\n\n"
        "3) If NO to step 1: Is the entire goal complete?\n"
        "   - Check Goal description in system prompt - are ALL steps done?\n"
        "   - Check recent conversation for completion indicators ('finalized', 'complete', etc.)\n"
        f"   - If complete -> {generate_toolchain_complete_guidance()}\n"
        "   - If not complete -> identify next needed tool, go to step 2\n\n"
        "CRITICAL RULES:\n"
        "• RESPOND WITH JSON ONLY - NO TEXT BEFORE OR AFTER THE JSON OBJECT\n"
        "• Your response must start with '{' and end with '}' - nothing else\n"
        "• NEVER set next='question' without asking an actual question in your response\n"
        "• NEVER set tool=null when you're announcing you'll run a specific tool\n"
        "• If response contains 'let's proceed to get pricing' -> next='confirm', tool='list_prices'\n"
        "• If response contains 'Now adding X' -> next='confirm', tool='create_invoice_item'\n"
        "• Use conversation history to infer arguments (customer IDs, product IDs, etc.)\n"
        "• Use sensible defaults rather than asking users for technical parameters\n"
        "• Carry forward arguments between tools (same customer, same invoice, etc.)\n"
        "• If force_confirm='False' in history, be declarative, don't ask permission\n\n"
        "EXAMPLES:\n"
        "WRONG: response='let\\'s get pricing', next='question', tool=null\n"
        "RIGHT: response='let\\'s get pricing', next='confirm', tool='list_prices'\n"
        "WRONG: response='adding pizza', next='question', tool='create_invoice_item'\n"
        "RIGHT: response='adding pizza', next='confirm', tool='create_invoice_item'\n"
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
    prompt_lines.append("=== FINAL REMINDER ===")
    prompt_lines.append("RESPOND WITH VALID JSON ONLY. NO ADDITIONAL TEXT.")
    prompt_lines.append("")
    if raw_json is not None:
        prompt_lines.append("Validate the provided JSON and return ONLY corrected JSON.")
    else:
        prompt_lines.append(
            "Return ONLY a valid JSON response. Start with '{' and end with '}'."
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
        return 'Next should only be "pick-new-goal" if EVERY SINGLE STEP in the Goal description has been completed (check the system prompt Goal section carefully), or the user explicitly requested to pick a new goal. If any step is missing (like customer creation, invoice creation, or payment processing), continue with the next required tool.'
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
        return "If no more tools are needed for the current goal (EVERY step in the Goal description has been completed AND user_confirmed_tool_run has been run for all required tools), set next='pick-new-goal' and tool=null to allow the user to choose their next action."
    else:
        return "If no more tools are needed (EVERY step in the Goal description has been completed AND user_confirmed_tool_run has been run for all), set next='done' and tool=null."
