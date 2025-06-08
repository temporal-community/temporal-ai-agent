import os

from models.tool_definitions import MCPServerDefinition


def get_stripe_mcp_server_definition(included_tools: list[str]) -> MCPServerDefinition:
    """
    Returns a Stripe MCP server definition with customizable included tools.

    Args:
        included_tools: List of tool names to include from the Stripe MCP server

    Returns:
        MCPServerDefinition configured for Stripe
    """
    return MCPServerDefinition(
        name="stripe-mcp",
        command="npx",
        args=[
            "-y",
            "@stripe/mcp",
            "--tools=all",
            f"--api-key={os.getenv('STRIPE_API_KEY')}",
        ],
        env=None,
        included_tools=included_tools,
    )
