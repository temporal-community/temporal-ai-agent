from workflows import ToolsData


def generate_genai_prompt_from_tools_data(
    tools_data: ToolsData, conversation_history: str
) -> str:
    """
    Generates a prompt describing the tools and the instructions for the AI
    assistant, using the conversation history provided.
    """
    prompt_lines = []

    prompt_lines.append(
        "You are an AI assistant that must determine all required arguments"
    )
    prompt_lines.append("for the tools to achieve the user's goal.\n")
    prompt_lines.append("Conversation history so far:")
    prompt_lines.append(conversation_history)
    prompt_lines.append("")

    # List all tools and their arguments
    for tool in tools_data.tools:
        prompt_lines.append(f"Tool to run: {tool.name}")
        prompt_lines.append(f"Description: {tool.description}")
        prompt_lines.append("Arguments needed:")
        for arg in tool.arguments:
            prompt_lines.append(f" - {arg.name} ({arg.type}): {arg.description}")
        prompt_lines.append("")

    prompt_lines.append("Instructions:")
    prompt_lines.append(
        "1. You need to ask the user (or confirm with them) for each argument required by the tools above."
    )
    prompt_lines.append(
        "2. If you do not yet have a specific argument value, ask the user for it."
    )
    prompt_lines.append(
        "3. Once you have all arguments, read them back to confirm with the user before yielding to the tool to take action.\n"
    )
    prompt_lines.append(
        'Your response must be valid JSON in the format: {"response": "<ai response>", "next": "<question|confirm>", '
        + '"tool": "<tool_name>", "arg1": "value1", "arg2": "value2"}" where args are the arguments for the tool (or null if unknown so far)."'
    )
    prompt_lines.append(
        '- Your goal is to convert the AI responses into filled args in the JSON and once all args are filled, confirm with the user.".'
    )
    prompt_lines.append(
        '- If you still need information from the user, use "next": "question".'
    )
    prompt_lines.append(
        '- If you have enough information and are confirming, use "next": "confirm". This is the final step once you have filled all args.'
    )
    prompt_lines.append(
        '- Example of a good answer: {"response": "It seems we have all the information needed to search for flights. You will be flying from <city> to <city> from <date> to <date>. Is this correct?", "args":{"origin": "Seattle", "destination": "San Francisco", "dateFrom": "2025-01-04", "dateTo": "2025-01-08"}, "next": "confirm", "tool": "<toolName>" }'
    )
    prompt_lines.append("- Return valid JSON without special characters.")
    prompt_lines.append("")
    prompt_lines.append("Begin by prompting or confirming the necessary details.")

    return "\n".join(prompt_lines)


def generate_json_validation_prompt_from_tools_data(
    tools_data: ToolsData, conversation_history: str, raw_json: str
) -> str:
    """
    Generates a prompt instructing the AI to:
      1. Check that the given raw JSON is syntactically valid.
      2. Ensure the 'tool' matches one of the defined tools in tools_data.
      3. Confirm or correct that all required arguments are present and make sense.
      4. Return a corrected JSON if possible.
    """
    prompt_lines = []

    prompt_lines.append(
        "You are an AI assistant that must validate the following JSON."
    )
    prompt_lines.append("It may be malformed or incomplete.")
    prompt_lines.append("You also have a list of tools and their required arguments.")
    prompt_lines.append(
        "You must ensure the JSON is valid and matches these definitions.\n"
    )

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
        "2. Does the 'tool' field match one of the tools in Tools Definitions? If not, correct or note the mismatch."
    )
    prompt_lines.append(
        "3. Do the arguments under 'args' correspond exactly to the required arguments for that tool? Are they present and valid? If not, set them to null or correct them."
    )
    prompt_lines.append(
        "4. Confirm the 'response' and 'next' fields are present, if applicable, per the desired JSON structure."
    )
    prompt_lines.append(
        "5. If something is missing or incorrect, fix it in the final JSON output or explain what is missing."
    )
    prompt_lines.append(
        "6. You can and should take values from the response, parse them and insert them into JSON args where possible. Carefully parse the history and the latest response to fill in the args."
    )
    prompt_lines.append("")
    prompt_lines.append(
        "Return your response in valid JSON. DO NOT RETURN ANYTHING EXCEPT VALID JSON IN THE CORRECT FORMAT. No editorializing or comments on the JSON."
    )
    prompt_lines.append("The final output must:")
    prompt_lines.append(
        '- Provide the corrected JSON if you can fix it, using the format {"response": "...", "next": "...", "tool": "...", "args": {...}}.'
    )
    prompt_lines.append(
        '- If you cannot correct it then provide a skeleton JSON structure with the original "response" value inside.\n'
    )
    prompt_lines.append("Conversation history so far:")
    prompt_lines.append(conversation_history)

    prompt_lines.append("Begin validating now.")

    return "\n".join(prompt_lines)
