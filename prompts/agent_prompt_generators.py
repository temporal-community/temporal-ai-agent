from models.tool_definitions import ToolsData
from typing import Optional
import json


def generate_genai_prompt(
    tools_data: ToolsData, conversation_history: str, raw_json: Optional[str] = None
) -> str:
    """
    Generates a concise prompt for producing or validating JSON instructions.
    """
    prompt_lines = []

    # Intro / Role
    prompt_lines.append(
        "You are an AI assistant that must produce or validate JSON instructions "
        "to properly call a set of tools. Respond with valid JSON only."
    )

    # Conversation History
    prompt_lines.append("=== Conversation History ===")
    prompt_lines.append(
        "Use this history to understand needed tools, arguments, and the user's goals:"
    )
    prompt_lines.append("BEGIN CONVERSATION HISTORY")
    prompt_lines.append(json.dumps(conversation_history, indent=2))
    prompt_lines.append("END CONVERSATION HISTORY")
    prompt_lines.append("")

    # Tools Definitions
    prompt_lines.append("=== Tools Definitions ===")
    prompt_lines.append(f"There are {len(tools_data.tools)} available tools:")
    prompt_lines.append(", ".join([t.name for t in tools_data.tools]))
    prompt_lines.append("")
    for tool in tools_data.tools:
        prompt_lines.append(f"Tool name: {tool.name}")
        prompt_lines.append(f"  Description: {tool.description}")
        prompt_lines.append("  Required args:")
        for arg in tool.arguments:
            prompt_lines.append(f"    - {arg.name} ({arg.type}): {arg.description}")
        prompt_lines.append("")

    # Instructions for JSON Generation
    prompt_lines.append("=== Instructions for JSON Generation ===")
    prompt_lines.append(
        "Your JSON format must be:\n"
        "{\n"
        '  "response": "<plain text>",\n'
        '  "next": "<question|confirm|done>",\n'
        '  "tool": "<tool_name or null>",\n'
        '  "args": {\n'
        '    "<arg1>": "<value1 or null>",\n'
        '    "<arg2>": "<value2 or null>",\n'
        "    ...\n"
        "  }\n"
        "}"
    )
    prompt_lines.append(
        "1. You may call multiple tools sequentially. Each requires specific arguments.\n"
        '2. If ANY required argument is missing, use "next": "question" and prompt the user.\n'
        '3. If all required arguments are known, use "next": "confirm" and set "tool" to the tool name.\n'
        '4. If no further actions are needed, use "next": "done" and "tool": "null".\n'
        '5. Keep "response" short and user-friendly. Do not include any metadata or editorializing.\n'
    )

    # Validation Task (Only if raw_json is provided)
    if raw_json is not None:
        prompt_lines.append("")
        prompt_lines.append("=== Validation Task ===")
        prompt_lines.append("Validate and correct the following JSON if needed:")
        prompt_lines.append(json.dumps(raw_json, indent=2))
        prompt_lines.append("")
        prompt_lines.append(
            "Check syntax, ensure 'tool' is correct or 'null', verify 'args' are valid, "
            'and set "next" appropriately based on missing or complete args.'
        )
        prompt_lines.append("Return only the corrected JSON, no extra text.")

    # Common Reminders and Examples
    prompt_lines.append("")
    prompt_lines.append("=== Usage Examples ===")
    prompt_lines.append(
        "Example for missing args (needs user input):\n"
        "{\n"
        '  "response": "I need your departure city.",\n'
        '  "next": "question",\n'
        '  "tool": "SearchFlights",\n'
        '  "args": {\n'
        '    "origin": null,\n'
        '    "destination": "Melbourne",\n'
        '    "dateDepart": "2025-03-26",\n'
        '    "dateReturn": "2025-04-20"\n'
        "  }\n"
        "}"
    )
    prompt_lines.append(
        "Example for confirmed args:\n"
        "{\n"
        '  "response": "All arguments are set.",\n'
        '  "next": "confirm",\n'
        '  "tool": "SearchFlights",\n'
        '  "args": {\n'
        '    "origin": "Seattle",\n'
        '    "destination": "Melbourne",\n'
        '    "dateDepart": "2025-03-26",\n'
        '    "dateReturn": "2025-04-20"\n'
        "  }\n"
        "}"
    )
    prompt_lines.append(
        "Example when fully done:\n"
        "{\n"
        '  "response": "All tools completed successfully. Final result: <insert result here>",\n'
        '  "next": "done",\n'
        '  "tool": "",\n'
        '  "args": {}\n'
        "}"
    )

    # Prompt Start
    if raw_json is not None:
        prompt_lines.append("")
        prompt_lines.append("Begin by validating the provided JSON if necessary.")
    else:
        prompt_lines.append("")
        prompt_lines.append(
            "Begin by producing a valid JSON response for the next step."
        )

    return "\n".join(prompt_lines)
