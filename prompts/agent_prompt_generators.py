from models.tool_definitions import ToolsData


def generate_genai_prompt_from_tools_data(
    tools_data: ToolsData, conversation_history: str
) -> str:
    """
    Generates a prompt describing the tools and the instructions for the AI
    assistant, using the conversation history provided, allowing for multiple
    tools and a 'done' state.
    """
    prompt_lines = []

    prompt_lines.append(
        "You are an AI assistant that must determine all required arguments "
        "for the tools to achieve the user's goal. "
    )
    prompt_lines.append("")
    prompt_lines.append(
        "Conversation history so far. \nANALYZE THIS HISTORY TO DETERMINE WHICH ARGUMENTS TO PRE-FILL AS SPECIFIED FOR THE TOOL BELOW: "
    )
    prompt_lines.append(conversation_history)
    prompt_lines.append("")

    # List all tools and their arguments
    prompt_lines.append("Available tools and their required arguments:")
    for tool in tools_data.tools:
        prompt_lines.append(f"- Tool name: {tool.name}")
        prompt_lines.append(f"  Description: {tool.description}")
        prompt_lines.append("  Arguments needed:")
        for arg in tool.arguments:
            prompt_lines.append(f"    - {arg.name} ({arg.type}): {arg.description}")
        prompt_lines.append("")

    prompt_lines.append("Instructions:")
    prompt_lines.append(
        "1. You may call multiple tools in sequence if needed, each requiring certain arguments. "
        "Ask the user for missing details when necessary. "
    )
    prompt_lines.append(
        "2. If you do not yet have a specific argument value, ask the user for it by setting 'next': 'question'."
    )
    prompt_lines.append(
        "3. Once you have enough information for a particular tool, respond with 'next': 'confirm' and include the tool name in 'tool'."
    )
    prompt_lines.append(
        "4. If you have completed all necessary tools (no more actions needed), use 'next': 'done' in your JSON response ."
    )
    prompt_lines.append(
        "5. Your response must be valid JSON in this format:\n"
        "   {\n"
        '       "response": "<plain text to user>",\n'
        '       "next": "<question|confirm|done>",\n'
        '       "tool": "<tool_name or none>",\n'
        '       "args": {\n'
        '           "<arg1>": "<value1>",\n'
        '           "<arg2>": "<value2>", ...\n'
        "       }\n"
        "   }\n"
        "   where 'args' are the arguments for the tool (or empty if not needed)."
    )
    prompt_lines.append(
        "6. If you still need information from the user, use 'next': 'question'. "
        "If you have enough info for a specific tool, use 'next': 'confirm'. "
        "Do NOT use 'next': 'confirm' until you have all necessary arguments (i.e. they're NOT 'null') ."
        "If you are finished with all tools, use 'next': 'done'."
    )
    prompt_lines.append(
        "7. Keep responses in plain text. Return valid JSON without extra commentary."
    )
    prompt_lines.append("")
    prompt_lines.append(
        "Begin by prompting or confirming the necessary details. If any are missing (null) ensure you ask for them."
    )

    return "\n".join(prompt_lines)


def generate_json_validation_prompt_from_tools_data(
    tools_data: ToolsData, conversation_history: str, raw_json: str
) -> str:
    """
    Generates a prompt instructing the AI to:
      1. Check that the given raw JSON is syntactically valid.
      2. Ensure the 'tool' matches one of the defined tools or is 'none' if no tool is needed.
      3. Confirm or correct that all required arguments are present or set to null if missing.
      4. Return a corrected JSON if possible.
      5. Accept 'next' as one of 'question', 'confirm', or 'done'.
    """
    prompt_lines = []

    prompt_lines.append(
        "You are an AI assistant that must validate the following JSON."
    )
    prompt_lines.append("It may be malformed or incomplete.")
    prompt_lines.append("You also have a list of tools and their required arguments.")
    prompt_lines.append(
        "You must ensure the JSON is valid and matches these definitions."
    )
    prompt_lines.append("")

    prompt_lines.append("== Tools Definitions ==")
    for tool in tools_data.tools:
        prompt_lines.append(f"Tool name: {tool.name}")
        prompt_lines.append(f"  Description: {tool.description}")
        prompt_lines.append("  Arguments required:")
        for arg in tool.arguments:
            prompt_lines.append(f"    - {arg.name} ({arg.type}): {arg.description}")
        prompt_lines.append("")

    prompt_lines.append("== JSON to Validate ==")
    prompt_lines.append(raw_json)
    prompt_lines.append("")

    prompt_lines.append("Validation checks:")
    prompt_lines.append("1. Is the JSON syntactically valid? If not, fix it.")
    prompt_lines.append(
        "2. Does the 'tool' field match one of the tools above (or 'none')?"
    )
    prompt_lines.append(
        "3. Do the 'args' correspond exactly to the required arguments for that tool? "
        "If arguments are missing, set them to null or correct them if possible."
    )
    prompt_lines.append(
        "4. Check the 'response' field is present. The user-facing text can be corrected but not removed."
    )
    prompt_lines.append(
        "5. 'next' should be one of 'question', 'confirm', or 'done' (if no more actions)."
        "Do NOT use 'next': 'confirm' until you have all args. If there are any args that are null then next='question'). "
    )
    prompt_lines.append(
        "6. If any of args is 'null' then ensure next = 'question' and that your response asks for this information from the user. "
    )
    prompt_lines.append(
        "7. If all tools mentioned above have 'completed successfully' (check the history) then next should be 'done'. "
    )
    prompt_lines.append(
        "Use the conversation history to parse known data for filling 'args' if possible. "
    )
    prompt_lines.append("")
    prompt_lines.append(
        "Return only valid JSON in the format:\n"
        "{\n"
        '  "response": "...",\n'
        '  "next": "question|confirm|done",\n'
        '  "tool": "<existing-tool-name-or-none>",\n'
        '  "args": { ... }\n'
        "}"
    )
    prompt_lines.append(
        "No additional commentary or explanation. Just the corrected JSON. "
    )
    prompt_lines.append("")
    prompt_lines.append("Conversation history so far:")
    prompt_lines.append(conversation_history)
    prompt_lines.append(
        "\nIMPORTANT: ANALYZE THIS HISTORY TO DETERMINE WHICH ARGUMENTS TO PRE-FILL IN THE JSON RESPONSE. "
    )
    prompt_lines.append("")
    prompt_lines.append("Begin validating now. ")

    return "\n".join(prompt_lines)
