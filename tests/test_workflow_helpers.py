import pytest

from models.tool_definitions import (
    AgentGoal,
    MCPServerDefinition,
    ToolArgument,
    ToolDefinition,
)
from workflows.workflow_helpers import is_mcp_tool


def make_goal(with_mcp: bool) -> AgentGoal:
    tools = [ToolDefinition(name="AddToCart", description="", arguments=[])]
    mcp_def = None
    if with_mcp:
        mcp_def = MCPServerDefinition(
            name="stripe", command="python", args=["server.py"]
        )
    return AgentGoal(
        id="g",
        category_tag="test",
        agent_name="Test",
        agent_friendly_description="",
        tools=tools,
        mcp_server_definition=mcp_def,
    )


def test_is_mcp_tool_recognizes_native():
    goal = make_goal(True)
    assert not is_mcp_tool("AddToCart", goal)


def test_is_mcp_tool_recognizes_mcp():
    goal = make_goal(True)
    assert is_mcp_tool("list_products", goal)
