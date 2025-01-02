from models.tool_definitions import ToolsData
from typing import Optional
import json


def generate_genai_prompt(
    tools_data: ToolsData, conversation_history: str, raw_json: Optional[str] = None
) -> str:
    """
    Generates json containing a unified prompt for an AI system to:
      - Understand the conversation so far.
      - Know which tools exist and their arguments.
      - Produce or validate JSON instructions accordingly.

    :param tools_data: An object containing your tool definitions.
    :param conversation_history: The user's conversation history.
    :param raw_json: The existing JSON to validate/correct (if any).
    :return: A json containing the merged instructions.
    """

    prompt_lines = []

    # Intro / Role
    prompt_lines.append(
        "You are an AI assistant that must produce or validate JSON instructions "
        "for a set of tools in order to achieve the user's goals."
    )
    prompt_lines.append("")

    # Conversation History
    prompt_lines.append("=== Conversation History ===")
    prompt_lines.append(
        "Analyze this history for context on tool usage, known arguments, and what's left to do."
    )
    prompt_lines.append(conversation_history)
    prompt_lines.append("")

    # Tools Definitions
    prompt_lines.append("=== Tools Definitions ===")
    for tool in tools_data.tools:
        prompt_lines.append(f"Tool name: {tool.name}")
        prompt_lines.append(f"  Description: {tool.description}")
        prompt_lines.append("  Required arguments:")
        for arg in tool.arguments:
            prompt_lines.append(f"    - {arg.name} ({arg.type}): {arg.description}")
        prompt_lines.append("")

    # Instructions for Generating JSON (Always Shown)
    prompt_lines.append("=== Instructions for JSON Generation ===")
    prompt_lines.append(
        "1. You may sequentially call multiple tools, each requiring specific arguments."
    )
    prompt_lines.append(
        "2. If any required argument is missing, set 'next': 'question' and ask the user for it."
    )
    prompt_lines.append(
        "3. Once all arguments for a tool are known, set 'next': 'confirm' with 'tool' set to that tool's name."
    )
    prompt_lines.append("4. If no further actions are required, set 'next': 'done'.")
    prompt_lines.append(
        "5. Always respond with valid JSON in this format:\n"
        "{\n"
        '  "response": "<plain text>",\n'
        '  "next": "<question|confirm|done>",\n'
        '  "tool": "<tool_name or none>",\n'
        '  "args": {\n'
        '    "<arg1>": "<value1 or null>",\n'
        '    "<arg2>": "<value2 or null>",\n'
        "    ...\n"
        "  }\n"
        "}"
    )
    prompt_lines.append(
        "6. Use 'next': 'question' if you lack any required arguments based on the history and prompt. "
        "Use 'next': 'confirm' only if NO arguments are missing. "
        "Use 'next': 'done' if no more tool calls are needed."
    )
    prompt_lines.append(
        "7. Keep 'response' user-friendly with no extra commentary. Stick to valid JSON syntax. "
        "Your goal is to guide the user through the running of these tools and elicit missing information."
    )
    prompt_lines.append("")

    # Instructions for Validation (Only if raw_json is provided)
    if raw_json is not None:
        prompt_lines.append("=== Validation Task ===")
        prompt_lines.append(
            "We have an existing JSON that may be malformed or incomplete. Validate and correct if needed."
        )
        prompt_lines.append("")
        prompt_lines.append("=== JSON to Validate ===")
        prompt_lines.append(json.dumps(raw_json, indent=2))
        prompt_lines.append("")
        prompt_lines.append("Validation Checks:")
        prompt_lines.append("1. Fix any JSON syntax errors.")
        prompt_lines.append("2. Ensure 'tool' is one of the defined tools or 'none'.")
        prompt_lines.append(
            "3. Check 'args' matches the required arguments for that tool; fill in from context or set null if unknown."
        )
        prompt_lines.append("4. Ensure 'response' is present (plain user-facing text).")
        prompt_lines.append(
            "5. Ensure 'next' is one of 'question', 'confirm', 'done'. "
            "Use 'question' if required args are still null, 'confirm' if all args are set, "
            "and 'done' if no more actions remain."
        )
        prompt_lines.append(
            "6. Use the conversation history to see if arguments can be inferred."
        )
        prompt_lines.append(
            "7. Return only the fixed JSON if changes are required, with no extra commentary."
        )

    # Final Guidance
    if raw_json is not None:
        prompt_lines.append("")
        prompt_lines.append(
            "Begin by validating (and correcting) the JSON above, if needed."
        )
    else:
        prompt_lines.append("")
        prompt_lines.append(
            "Begin by generating a valid JSON response for the next step."
        )

    prompt_lines.append(
        "REMINDER: If any required argument is missing, set 'next': 'question' and ask the user for it."
    )
    prompt_lines.append(
        """
        Example JSON:
            {
                "args": {
                "dateDepart": "2025-03-26",
                "dateReturn": "2025-04-20",
                "destination": "Melbourne",
                "origin": null
                },
                "next": "question",
                "response": "I need to know where you're flying from. What's your departure city?",
                "tool": "SearchFlights"
            }
        """
    )

    return "\n".join(prompt_lines)
