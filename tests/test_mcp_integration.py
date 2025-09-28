import asyncio
import uuid
from collections import deque
from typing import Sequence
from unittest.mock import patch

import pytest
from temporalio import activity
from temporalio.client import Client
from temporalio.common import RawValue
from temporalio.testing import ActivityEnvironment
from temporalio.worker import Worker

from activities.tool_activities import _convert_args_types, mcp_list_tools
from models.data_types import (
    AgentGoalWorkflowParams,
    CombinedInput,
    EnvLookupInput,
    EnvLookupOutput,
    ToolPromptInput,
    ValidationInput,
    ValidationResult,
)
from models.tool_definitions import AgentGoal, MCPServerDefinition, ToolDefinition
from workflows.agent_goal_workflow import AgentGoalWorkflow
from workflows.workflow_helpers import is_mcp_tool


class DummySession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def initialize(self):
        pass

    async def list_tools(self):
        class Tool:
            def __init__(self, name):
                self.name = name
                self.description = f"desc {name}"
                self.inputSchema = {}

        return type(
            "Resp", (), {"tools": [Tool("list_products"), Tool("create_customer")]}
        )()


def test_convert_args_types_basic():
    args = {
        "count": "5",
        "price": "12.5",
        "flag_true": "true",
        "flag_false": "false",
        "name": "pizza",
        "already_int": 2,
    }
    result = _convert_args_types(args)
    assert result["count"] == 5 and isinstance(result["count"], int)
    assert result["price"] == 12.5 and isinstance(result["price"], float)
    assert result["flag_true"] is True
    assert result["flag_false"] is False
    assert result["name"] == "pizza"
    assert result["already_int"] == 2


def test_is_mcp_tool_identification():
    server_def = MCPServerDefinition(name="test", command="python", args=["server.py"])
    goal = AgentGoal(
        id="g",
        category_tag="food",
        agent_name="agent",
        agent_friendly_description="",
        description="",
        tools=[ToolDefinition(name="AddToCart", description="", arguments=[])],
        starter_prompt="",
        example_conversation_history="",
        mcp_server_definition=server_def,
    )

    assert is_mcp_tool("list_products", goal) is True
    assert is_mcp_tool("AddToCart", goal) is False
    no_mcp_goal = AgentGoal(
        id="g2",
        category_tag="food",
        agent_name="agent",
        agent_friendly_description="",
        description="",
        tools=[],
        starter_prompt="",
        example_conversation_history="",
        mcp_server_definition=None,
    )
    assert is_mcp_tool("list_products", no_mcp_goal) is False


@pytest.mark.asyncio
async def test_mcp_list_tools_success():
    server_def = MCPServerDefinition(name="test", command="python", args=["server.py"])

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def dummy_connection(command, args, env):
        yield None, None

    with patch(
        "activities.tool_activities._build_connection", return_value={"type": "stdio"}
    ), patch("activities.tool_activities._stdio_connection", dummy_connection), patch(
        "activities.tool_activities.ClientSession", lambda r, w: DummySession()
    ):
        activity_env = ActivityEnvironment()
        result = await activity_env.run(mcp_list_tools, server_def, ["list_products"])
        assert result["success"] is True
        assert result["filtered_count"] == 1
        assert "list_products" in result["tools"]


@pytest.mark.asyncio
async def test_mcp_list_tools_failure():
    server_def = MCPServerDefinition(name="test", command="python", args=["server.py"])

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def failing_connection(*args, **kwargs):
        raise RuntimeError("conn fail")
        yield None, None

    with patch(
        "activities.tool_activities._build_connection", return_value={"type": "stdio"}
    ), patch("activities.tool_activities._stdio_connection", failing_connection):
        activity_env = ActivityEnvironment()
        result = await activity_env.run(mcp_list_tools, server_def)
        assert result["success"] is False
        assert "conn fail" in result["error"]


@pytest.mark.asyncio
async def test_workflow_loads_mcp_tools_dynamically(client: Client):
    """Workflow should load MCP tools and add them to the goal."""
    task_queue_name = str(uuid.uuid4())
    server_def = MCPServerDefinition(name="test", command="python", args=["srv.py"])
    goal = AgentGoal(
        id="g_mcp",
        category_tag="food",
        agent_name="agent",
        agent_friendly_description="",
        description="",
        tools=[],
        starter_prompt="",
        example_conversation_history="",
        mcp_server_definition=server_def,
    )
    combined_input = CombinedInput(
        agent_goal=goal,
        tool_params=AgentGoalWorkflowParams(
            conversation_summary=None, prompt_queue=deque()
        ),
    )

    @activity.defn(name="get_wf_env_vars")
    async def mock_get_wf_env_vars(input: EnvLookupInput) -> EnvLookupOutput:
        return EnvLookupOutput(show_confirm=True, multi_goal_mode=True)

    @activity.defn(name="mcp_list_tools")
    async def mock_mcp_list_tools(
        server_definition: MCPServerDefinition, include_tools=None
    ):
        return {
            "server_name": server_definition.name,
            "success": True,
            "tools": {
                "list_products": {
                    "name": "list_products",
                    "description": "",
                    "inputSchema": {},
                },
            },
            "total_available": 1,
            "filtered_count": 1,
        }

    async with Worker(
        client,
        task_queue=task_queue_name,
        workflows=[AgentGoalWorkflow],
        activities=[mock_get_wf_env_vars, mock_mcp_list_tools],
    ):
        handle = await client.start_workflow(
            AgentGoalWorkflow.run,
            combined_input,
            id=str(uuid.uuid4()),
            task_queue=task_queue_name,
        )

        # Wait until the MCP tools have been added
        for _ in range(10):
            updated_goal = await handle.query(AgentGoalWorkflow.get_agent_goal)
            if any(t.name == "list_products" for t in updated_goal.tools):
                break
            await asyncio.sleep(0.1)
        else:
            updated_goal = await handle.query(AgentGoalWorkflow.get_agent_goal)

        assert any(t.name == "list_products" for t in updated_goal.tools)

        await handle.signal(AgentGoalWorkflow.end_chat)
        await handle.result()


@pytest.mark.asyncio
async def test_mcp_tool_execution_flow(client: Client):
    """MCP tool execution should pass server_definition to activity."""
    task_queue_name = str(uuid.uuid4())
    server_def = MCPServerDefinition(name="test", command="python", args=["srv.py"])
    goal = AgentGoal(
        id="g_mcp_exec",
        category_tag="food",
        agent_name="agent",
        agent_friendly_description="",
        description="",
        tools=[],
        starter_prompt="",
        example_conversation_history="",
        mcp_server_definition=server_def,
    )
    combined_input = CombinedInput(
        agent_goal=goal,
        tool_params=AgentGoalWorkflowParams(
            conversation_summary=None, prompt_queue=deque()
        ),
    )

    captured: dict = {}

    @activity.defn(name="get_wf_env_vars")
    async def mock_get_wf_env_vars(input: EnvLookupInput) -> EnvLookupOutput:
        return EnvLookupOutput(show_confirm=True, multi_goal_mode=True)

    @activity.defn(name="agent_validatePrompt")
    async def mock_validate(prompt: ValidationInput) -> ValidationResult:
        return ValidationResult(validationResult=True, validationFailedReason={})

    @activity.defn(name="agent_toolPlanner")
    async def mock_planner(input: ToolPromptInput) -> dict:
        if "planner_called" not in captured:
            captured["planner_called"] = True
            return {
                "next": "confirm",
                "tool": "list_products",
                "args": {"limit": "5"},
                "response": "Listing products",
            }
        return {"next": "done", "response": "done"}

    @activity.defn(name="mcp_list_tools")
    async def mock_mcp_list_tools(
        server_definition: MCPServerDefinition, include_tools=None
    ):
        return {
            "server_name": server_definition.name,
            "success": True,
            "tools": {
                "list_products": {
                    "name": "list_products",
                    "description": "",
                    "inputSchema": {},
                },
            },
            "total_available": 1,
            "filtered_count": 1,
        }

    @activity.defn(name="dynamic_tool_activity", dynamic=True)
    async def mock_dynamic_tool_activity(args: Sequence[RawValue]) -> dict:
        payload = activity.payload_converter().from_payload(args[0].payload, dict)
        captured["dynamic_args"] = payload
        return {"tool": "list_products", "success": True, "content": {"ok": True}}

    async with Worker(
        client,
        task_queue=task_queue_name,
        workflows=[AgentGoalWorkflow],
        activities=[
            mock_get_wf_env_vars,
            mock_validate,
            mock_planner,
            mock_mcp_list_tools,
            mock_dynamic_tool_activity,
        ],
    ):
        handle = await client.start_workflow(
            AgentGoalWorkflow.run,
            combined_input,
            id=str(uuid.uuid4()),
            task_queue=task_queue_name,
        )

        await handle.signal(AgentGoalWorkflow.user_prompt, "show menu")
        await asyncio.sleep(0.5)
        await handle.signal(AgentGoalWorkflow.confirm)
        # Give workflow time to execute the MCP tool and finish
        await asyncio.sleep(0.5)
        result = await handle.result()
        print(result)

    assert "dynamic_args" in captured
    assert "server_definition" in captured["dynamic_args"]
    assert captured["dynamic_args"]["server_definition"]["name"] == server_def.name


@pytest.mark.asyncio
async def test_create_invoice_defaults_days_until_due(client: Client):
    """create_invoice should include a default days_until_due when missing."""
    task_queue_name = str(uuid.uuid4())
    server_def = MCPServerDefinition(name="test", command="python", args=["srv.py"])
    goal = AgentGoal(
        id="g_invoice_default",
        category_tag="food",
        agent_name="agent",
        agent_friendly_description="",
        description="",
        tools=[],
        starter_prompt="",
        example_conversation_history="",
        mcp_server_definition=server_def,
    )
    combined_input = CombinedInput(
        agent_goal=goal,
        tool_params=AgentGoalWorkflowParams(
            conversation_summary=None, prompt_queue=deque()
        ),
    )

    captured: dict = {}

    @activity.defn(name="get_wf_env_vars")
    async def mock_get_wf_env_vars(input: EnvLookupInput) -> EnvLookupOutput:
        return EnvLookupOutput(show_confirm=True, multi_goal_mode=True)

    @activity.defn(name="agent_validatePrompt")
    async def mock_validate(prompt: ValidationInput) -> ValidationResult:
        return ValidationResult(validationResult=True, validationFailedReason={})

    @activity.defn(name="agent_toolPlanner")
    async def mock_planner(input: ToolPromptInput) -> dict:
        if "planner_called" not in captured:
            captured["planner_called"] = True
            return {
                "next": "confirm",
                "tool": "create_invoice",
                "args": {"customer": "cus_123"},
                "response": "Creating invoice",
            }
        return {"next": "done", "response": "done"}

    @activity.defn(name="mcp_list_tools")
    async def mock_mcp_list_tools(
        server_definition: MCPServerDefinition, include_tools=None
    ):
        return {
            "server_name": server_definition.name,
            "success": True,
            "tools": {
                "create_invoice": {
                    "name": "create_invoice",
                    "description": "",
                    "inputSchema": {
                        "properties": {
                            "customer": {"type": "string"},
                            "days_until_due": {"type": "number"},
                        }
                    },
                },
            },
            "total_available": 1,
            "filtered_count": 1,
        }

    @activity.defn(name="dynamic_tool_activity", dynamic=True)
    async def mock_dynamic_tool_activity(args: Sequence[RawValue]) -> dict:
        payload = activity.payload_converter().from_payload(args[0].payload, dict)
        captured["dynamic_args"] = payload
        return {"tool": "create_invoice", "success": True, "content": {"ok": True}}

    async with Worker(
        client,
        task_queue=task_queue_name,
        workflows=[AgentGoalWorkflow],
        activities=[
            mock_get_wf_env_vars,
            mock_validate,
            mock_planner,
            mock_mcp_list_tools,
            mock_dynamic_tool_activity,
        ],
    ):
        handle = await client.start_workflow(
            AgentGoalWorkflow.run,
            combined_input,
            id=str(uuid.uuid4()),
            task_queue=task_queue_name,
        )

        await handle.signal(AgentGoalWorkflow.user_prompt, "make invoice")
        await asyncio.sleep(0.5)
        await handle.signal(AgentGoalWorkflow.confirm)
        await asyncio.sleep(0.5)
        await handle.result()

    assert "dynamic_args" in captured
    assert captured["dynamic_args"]["days_until_due"] == 7


@pytest.mark.asyncio
async def test_mcp_tool_failure_recorded(client: Client):
    """Failure of an MCP tool should be recorded in conversation history."""
    task_queue_name = str(uuid.uuid4())
    server_def = MCPServerDefinition(name="test", command="python", args=["srv.py"])
    goal = AgentGoal(
        id="g_mcp_fail",
        category_tag="food",
        agent_name="agent",
        agent_friendly_description="",
        description="",
        tools=[],
        starter_prompt="",
        example_conversation_history="",
        mcp_server_definition=server_def,
    )
    combined_input = CombinedInput(
        agent_goal=goal,
        tool_params=AgentGoalWorkflowParams(
            conversation_summary=None, prompt_queue=deque()
        ),
    )

    @activity.defn(name="get_wf_env_vars")
    async def mock_get_wf_env_vars(input: EnvLookupInput) -> EnvLookupOutput:
        return EnvLookupOutput(show_confirm=True, multi_goal_mode=True)

    @activity.defn(name="agent_validatePrompt")
    async def mock_validate(prompt: ValidationInput) -> ValidationResult:
        return ValidationResult(validationResult=True, validationFailedReason={})

    @activity.defn(name="agent_toolPlanner")
    async def mock_planner(input: ToolPromptInput) -> dict:
        return {
            "next": "confirm",
            "tool": "list_products",
            "args": {},
            "response": "Listing products",
        }

    @activity.defn(name="mcp_list_tools")
    async def mock_mcp_list_tools(
        server_definition: MCPServerDefinition, include_tools=None
    ):
        return {
            "server_name": server_definition.name,
            "success": True,
            "tools": {
                "list_products": {
                    "name": "list_products",
                    "description": "",
                    "inputSchema": {},
                },
            },
            "total_available": 1,
            "filtered_count": 1,
        }

    @activity.defn(name="dynamic_tool_activity", dynamic=True)
    async def failing_dynamic_tool(args: Sequence[RawValue]) -> dict:
        return {
            "tool": "list_products",
            "success": False,
            "error": "Connection timed out",
        }

    async with Worker(
        client,
        task_queue=task_queue_name,
        workflows=[AgentGoalWorkflow],
        activities=[
            mock_get_wf_env_vars,
            mock_validate,
            mock_planner,
            mock_mcp_list_tools,
            failing_dynamic_tool,
        ],
    ):
        handle = await client.start_workflow(
            AgentGoalWorkflow.run,
            combined_input,
            id=str(uuid.uuid4()),
            task_queue=task_queue_name,
        )

        await handle.signal(AgentGoalWorkflow.user_prompt, "show menu")
        await asyncio.sleep(0.5)
        await handle.signal(AgentGoalWorkflow.confirm)
        # Give workflow time to record the failure result
        await asyncio.sleep(0.5)
        await handle.signal(AgentGoalWorkflow.end_chat)
        result = await handle.result()

    import json

    try:
        history = json.loads(result.replace("'", '"'))
    except Exception:
        history = eval(result)

    assert any(
        msg["actor"] == "tool_result" and not msg["response"].get("success", True)
        for msg in history["messages"]
    )
