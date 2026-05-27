"""Workflow-side helpers for invoking MCP tools through the dispatcher.

Workflows should call :func:`invoke_mcp_tool` instead of building an
``execute_activity`` call by hand: it keeps the activity name, retry policy,
and timeouts consistent across every MCP tool boundary in the system.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, Optional, Union

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError

with workflow.unsafe.imports_passed_through():
    from activities.mcp_dispatcher import build_mcp_activity_name, mcp_retry_policy
    from models.mcp_types import MCPToolError, MCPToolInvocation, MCPToolResult
    from models.tool_definitions import MCPServerDefinition


# Default timeouts mirror the existing TOOL_ACTIVITY_* limits in
# workflows/workflow_helpers.py, but are exposed here so consumers can tune
# them per workflow.
MCP_TOOL_START_TO_CLOSE_TIMEOUT = timedelta(seconds=30)
MCP_TOOL_SCHEDULE_TO_CLOSE_TIMEOUT = timedelta(minutes=30)


async def invoke_mcp_tool(
    *,
    tool_name: str,
    arguments: Dict[str, Any],
    server_definition: Union[MCPServerDefinition, Dict[str, Any]],
    retry_policy: Optional[RetryPolicy] = None,
    start_to_close_timeout: timedelta = MCP_TOOL_START_TO_CLOSE_TIMEOUT,
    schedule_to_close_timeout: timedelta = MCP_TOOL_SCHEDULE_TO_CLOSE_TIMEOUT,
    summary: Optional[str] = None,
) -> MCPToolResult:
    """Execute one MCP tool via the dispatcher Activity and return a typed result.

    Failures that the dispatcher classifies as retryable will be retried by
    Temporal automatically. Failures that exhaust retries surface as an
    :class:`ActivityError`, which this helper converts into a structured
    :class:`MCPToolResult` so the workflow can continue, branch, or terminate
    cleanly without unwrapping nested exceptions.
    """
    server_name = _server_name(server_definition)
    activity_name = build_mcp_activity_name(server_name, tool_name)

    invocation = MCPToolInvocation(
        tool_name=tool_name,
        arguments=arguments,
        server_definition=server_definition,
        summary=summary,
    )

    try:
        raw = await workflow.execute_activity(
            activity_name,
            invocation,
            start_to_close_timeout=start_to_close_timeout,
            schedule_to_close_timeout=schedule_to_close_timeout,
            retry_policy=retry_policy or mcp_retry_policy(),
            summary=summary or f"MCP {server_name} → {tool_name}",
        )
    except ActivityError as exc:
        cause = exc.cause
        message = str(cause) if cause is not None else str(exc)
        error_type = type(cause).__name__ if cause is not None else "ActivityError"
        return MCPToolResult(
            tool=tool_name,
            success=False,
            error=MCPToolError(
                message=message,
                error_type=error_type,
                retryable=False,  # retries already exhausted at this point
            ),
        )

    return _result_from_dict(raw, tool_name)


def _server_name(
    server_definition: Union[MCPServerDefinition, Dict[str, Any]],
) -> str:
    if isinstance(server_definition, dict):
        return str(server_definition.get("name", "default"))
    return getattr(server_definition, "name", "default")


def _result_from_dict(raw: Dict[str, Any], tool_name: str) -> MCPToolResult:
    """Rehydrate a dispatcher response dict back into an :class:`MCPToolResult`."""
    if raw is None:
        return MCPToolResult(
            tool=tool_name,
            success=False,
            error=MCPToolError(
                message="MCP dispatcher returned no result",
                error_type="EmptyResult",
                retryable=False,
            ),
        )

    success = bool(raw.get("success"))
    if success:
        return MCPToolResult(
            tool=raw.get("tool", tool_name),
            success=True,
            content=raw.get("content"),
        )

    return MCPToolResult(
        tool=raw.get("tool", tool_name),
        success=False,
        error=MCPToolError(
            message=str(raw.get("error", "MCP tool reported failure")),
            error_type=str(raw.get("error_type", "MCPError")),
            retryable=bool(raw.get("retryable", False)),
            details=raw.get("error_details", {}) or {},
        ),
    )
