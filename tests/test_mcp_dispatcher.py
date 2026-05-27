"""Tests for the dynamic MCP dispatcher activity and sample chain workflow."""

import dataclasses
import uuid
from typing import Any, Dict, Sequence
from unittest.mock import patch

import pytest
from temporalio import activity
from temporalio.client import Client
from temporalio.common import RawValue
from temporalio.converter import default as default_converter
from temporalio.exceptions import ApplicationError
from temporalio.testing import ActivityEnvironment
from temporalio.worker import Worker

from activities.mcp_dispatcher import (
    MCP_ACTIVITY_PREFIX,
    build_mcp_activity_name,
    mcp_retry_policy,
    mcp_tool_dispatcher,
    parse_mcp_activity_name,
)
from models.mcp_types import MCPToolError, MCPToolInvocation, MCPToolResult
from models.tool_definitions import MCPServerDefinition
from workflows.mcp_agent_chain_workflow import (
    MCPAgentChainInput,
    MCPAgentChainOutput,
    MCPAgentChainWorkflow,
)

# ---------- Pure helper tests ---------------------------------------------


def test_build_and_parse_activity_name_roundtrip():
    name = build_mcp_activity_name("stripe", "create_invoice")
    assert name.startswith(MCP_ACTIVITY_PREFIX)
    parsed = parse_mcp_activity_name(name)
    assert parsed == {"server": "stripe", "tool": "create_invoice"}


def test_parse_activity_name_rejects_non_mcp():
    assert parse_mcp_activity_name("FindEvents") is None
    assert parse_mcp_activity_name("mcp__stripe") is None
    assert parse_mcp_activity_name("mcp____tool") is None


def test_mcp_retry_policy_marks_argument_errors_non_retryable():
    policy = mcp_retry_policy()
    assert "MCPInvalidArgumentError" in policy.non_retryable_error_types
    assert policy.maximum_attempts == 5


def test_mcp_tool_result_as_dict_round_trip():
    ok = MCPToolResult(tool="t", success=True, content={"a": 1})
    assert ok.as_dict() == {"tool": "t", "success": True, "content": {"a": 1}}

    err = MCPToolResult(
        tool="t",
        success=False,
        error=MCPToolError(
            message="boom",
            error_type="ConnectionError",
            retryable=True,
            details={"host": "x"},
        ),
    )
    d = err.as_dict()
    assert d["success"] is False
    assert d["error"] == "boom"
    assert d["error_type"] == "ConnectionError"
    assert d["retryable"] is True
    assert d["error_details"] == {"host": "x"}


# ---------- Dispatcher activity tests -------------------------------------


def _payload_for(invocation_dict: Dict[str, Any]) -> RawValue:
    """Create a RawValue payload from a dict using Temporal's default converter."""
    converter = default_converter().payload_converter
    payload = converter.to_payloads([invocation_dict])[0]
    return RawValue(payload=payload)


def _env_for_activity(activity_name: str) -> ActivityEnvironment:
    env = ActivityEnvironment()
    env.info = dataclasses.replace(env.info, activity_type=activity_name)
    return env


@pytest.mark.asyncio
async def test_dispatcher_returns_success_when_pool_succeeds():
    """Dispatcher converts a pooled-manager result into MCPToolResult shape."""
    server_def = MCPServerDefinition(name="srv", command="python", args=["s.py"])
    invocation_dict = {
        "tool_name": "list_things",
        "arguments": {"limit": 3},
        "server_definition": {
            "name": "srv",
            "command": "python",
            "args": ["s.py"],
            "connection_type": "stdio",
        },
    }
    payload = _payload_for(invocation_dict)

    async def fake_pool_call(invocation):
        return MCPToolResult(
            tool=invocation.tool_name,
            success=True,
            content=["a", "b"],
        )

    with patch(
        "activities.mcp_dispatcher._call_via_pooled_manager", side_effect=fake_pool_call
    ):
        env = _env_for_activity(build_mcp_activity_name(server_def.name, "list_things"))
        result = await env.run(mcp_tool_dispatcher, [payload])

    assert result["success"] is True
    assert result["content"] == ["a", "b"]
    assert result["tool"] == "list_things"


@pytest.mark.asyncio
async def test_dispatcher_raises_application_error_for_transport_failures():
    """A transport-level exception is re-raised as ApplicationError for retry."""
    invocation_dict = {
        "tool_name": "list_things",
        "arguments": {},
        "server_definition": {
            "name": "srv",
            "command": "python",
            "args": ["s.py"],
        },
    }
    payload = _payload_for(invocation_dict)

    async def fake_pool_call(invocation):
        raise ConnectionError("server reset")

    with patch(
        "activities.mcp_dispatcher._call_via_pooled_manager", side_effect=fake_pool_call
    ):
        env = _env_for_activity(build_mcp_activity_name("srv", "list_things"))
        with pytest.raises(ApplicationError) as excinfo:
            await env.run(mcp_tool_dispatcher, [payload])

    # Retryable transport errors should NOT be marked non_retryable.
    assert excinfo.value.non_retryable is False
    assert "server reset" in str(excinfo.value)


@pytest.mark.asyncio
async def test_dispatcher_rejects_missing_server_definition():
    """Missing server_definition is a non-retryable invalid-argument error."""
    invocation_dict = {"tool_name": "x", "arguments": {}}
    payload = _payload_for(invocation_dict)

    env = _env_for_activity(build_mcp_activity_name("srv", "x"))
    with pytest.raises(ApplicationError) as excinfo:
        await env.run(mcp_tool_dispatcher, [payload])

    assert excinfo.value.non_retryable is True
    assert excinfo.value.type == "MCPInvalidArgumentError"


# ---------- Sample chain workflow tests -----------------------------------


@pytest.mark.asyncio
async def test_mcp_agent_chain_runs_multiple_tools(client: Client):
    task_queue_name = str(uuid.uuid4())
    server_def = MCPServerDefinition(name="testsrv", command="python", args=["s.py"])

    calls: list = []

    @activity.defn(dynamic=True)
    async def fake_dispatcher(args: Sequence[RawValue]) -> Dict[str, Any]:
        activity_name = activity.info().activity_type
        payload = activity.payload_converter().from_payload(args[0].payload, dict)
        calls.append((activity_name, payload))
        # Simulate a successful response for every tool.
        return {
            "tool": activity_name.split("__")[-1],
            "success": True,
            "content": {"echo": payload.get("arguments")},
        }

    chain_input = MCPAgentChainInput(
        invocations=[
            MCPToolInvocation(
                tool_name="list_things",
                arguments={"limit": 2},
                server_definition=server_def,
            ),
            MCPToolInvocation(
                tool_name="create_thing",
                arguments={"name": "foo"},
                server_definition=server_def,
            ),
        ]
    )

    async with Worker(
        client,
        task_queue=task_queue_name,
        workflows=[MCPAgentChainWorkflow],
        activities=[fake_dispatcher],
    ):
        handle = await client.start_workflow(
            MCPAgentChainWorkflow.run,
            chain_input,
            id=str(uuid.uuid4()),
            task_queue=task_queue_name,
        )
        out: MCPAgentChainOutput = await handle.result()

    assert out.completed == 2
    assert out.failed == 0
    assert len(out.results) == 2
    activity_names = [name for name, _ in calls]
    assert activity_names == [
        build_mcp_activity_name(server_def.name, "list_things"),
        build_mcp_activity_name(server_def.name, "create_thing"),
    ]


@pytest.mark.asyncio
async def test_mcp_agent_chain_stops_on_failure(client: Client):
    task_queue_name = str(uuid.uuid4())
    server_def = MCPServerDefinition(name="testsrv", command="python", args=["s.py"])

    seen: list = []

    @activity.defn(dynamic=True)
    async def fake_dispatcher(args: Sequence[RawValue]) -> Dict[str, Any]:
        activity_name = activity.info().activity_type
        seen.append(activity_name)
        # First tool fails (non-retryable so chain stops fast), second never runs.
        return {
            "tool": activity_name.split("__")[-1],
            "success": False,
            "error": "thing went wrong",
            "error_type": "ToolFailure",
            "retryable": False,
        }

    chain_input = MCPAgentChainInput(
        invocations=[
            MCPToolInvocation(
                tool_name="first", arguments={}, server_definition=server_def
            ),
            MCPToolInvocation(
                tool_name="second", arguments={}, server_definition=server_def
            ),
        ],
        stop_on_failure=True,
    )

    async with Worker(
        client,
        task_queue=task_queue_name,
        workflows=[MCPAgentChainWorkflow],
        activities=[fake_dispatcher],
    ):
        handle = await client.start_workflow(
            MCPAgentChainWorkflow.run,
            chain_input,
            id=str(uuid.uuid4()),
            task_queue=task_queue_name,
        )
        out: MCPAgentChainOutput = await handle.result()

    assert out.completed == 0
    assert out.failed == 1
    assert len(out.results) == 1
    # The second tool must NOT have been dispatched.
    assert len(seen) == 1
    assert seen[0].endswith("__first")
