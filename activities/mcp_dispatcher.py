"""Dynamic Temporal-Activity dispatcher for MCP tools.

Every MCP tool the LLM chooses is executed as a dedicated Temporal Activity
through this module. The dispatcher is a single `@activity.defn(dynamic=True)`
function — Temporal dispatches by the *activity type name* the workflow uses
when it calls `workflow.execute_activity(...)`, so we get one boundary per
tool invocation in workflow history without having to predeclare every
possible MCP tool at worker startup.

Naming convention
-----------------
Workflows should invoke the activity using a deterministic name produced by
``build_mcp_activity_name(server_name, tool_name)`` — e.g.
``mcp__stripe__create_invoice``. The dispatcher parses the name back into the
``server``/``tool`` pair, so any MCP tool definition discovered at runtime can
be executed without further registration.

Result contract
---------------
The dispatcher always returns an :class:`MCPToolResult` (typed dataclass).
Transport-level exceptions are re-raised as ``ApplicationError`` so Temporal's
RetryPolicy can retry them; logical/non-retryable failures are folded into
``MCPToolResult(success=False, error=...)`` so the workflow can decide what to
do next without exploding the workflow history with retries.
"""

from __future__ import annotations

import inspect
from typing import Any, Dict, Optional, Sequence, Union

from temporalio import activity
from temporalio.common import RawValue, RetryPolicy
from temporalio.exceptions import ApplicationError

from models.mcp_types import MCPToolError, MCPToolInvocation, MCPToolResult
from models.tool_definitions import MCPServerDefinition

# Activity-name prefix that identifies an MCP-dispatcher activity invocation.
MCP_ACTIVITY_PREFIX = "mcp__"
_MCP_NAME_SEP = "__"

# Errors raised by the MCP transport that should NOT be retried because they
# indicate a misconfiguration rather than a transient failure.
NON_RETRYABLE_ERROR_TYPES = (
    "MCPToolNotFoundError",
    "MCPInvalidArgumentError",
)


def build_mcp_activity_name(server_name: str, tool_name: str) -> str:
    """Return the canonical Temporal activity type name for an MCP tool call.

    Example: ``build_mcp_activity_name("stripe", "create_invoice")`` returns
    ``"mcp__stripe__create_invoice"``.
    """
    # Sanitize: Temporal activity names should not contain whitespace.
    safe_server = (server_name or "default").strip().replace(" ", "_")
    safe_tool = (tool_name or "unknown").strip().replace(" ", "_")
    return f"{MCP_ACTIVITY_PREFIX}{safe_server}{_MCP_NAME_SEP}{safe_tool}"


def parse_mcp_activity_name(activity_name: str) -> Optional[Dict[str, str]]:
    """Inverse of :func:`build_mcp_activity_name`.

    Returns ``{"server": ..., "tool": ...}`` for a recognised dispatcher name,
    or ``None`` if the name doesn't follow the convention.
    """
    if not activity_name.startswith(MCP_ACTIVITY_PREFIX):
        return None
    remainder = activity_name[len(MCP_ACTIVITY_PREFIX) :]
    # Server names may not contain `__`; tools may contain a single underscore.
    if _MCP_NAME_SEP not in remainder:
        return None
    server, tool = remainder.split(_MCP_NAME_SEP, 1)
    if not server or not tool:
        return None
    return {"server": server, "tool": tool}


def mcp_retry_policy(
    *,
    initial_interval_seconds: int = 1,
    maximum_attempts: int = 5,
    backoff_coefficient: float = 2.0,
) -> RetryPolicy:
    """Default RetryPolicy for MCP tool activity invocations.

    Sensible defaults for IO-bound MCP tool calls: fast first retry, capped
    attempts, exponential backoff, and an explicit non-retryable error-type
    list (so a malformed argument doesn't get retried five times).
    """
    from datetime import timedelta

    return RetryPolicy(
        initial_interval=timedelta(seconds=initial_interval_seconds),
        backoff_coefficient=backoff_coefficient,
        maximum_attempts=maximum_attempts,
        non_retryable_error_types=list(NON_RETRYABLE_ERROR_TYPES),
    )


def _coerce_invocation(
    payload: Union[MCPToolInvocation, Dict[str, Any]],
    activity_name: str,
) -> MCPToolInvocation:
    """Accept either a typed invocation or a legacy dict-style payload."""
    if isinstance(payload, MCPToolInvocation):
        return payload

    if not isinstance(payload, dict):
        raise ApplicationError(
            f"Unsupported MCP invocation payload type: {type(payload).__name__}",
            type="MCPInvalidArgumentError",
            non_retryable=True,
        )

    # Legacy dict shape: {"tool_name": ..., "arguments": {...}, "server_definition": ...}
    # OR the flat shape used by the original dynamic_tool_activity where
    # `server_definition` sits next to the tool's own kwargs.
    if "arguments" in payload or "tool_name" in payload:
        tool_name = payload.get("tool_name") or _tool_name_from_activity(activity_name)
        arguments = payload.get("arguments", {})
        server_definition = payload.get("server_definition")
    else:
        arguments = {k: v for k, v in payload.items() if k != "server_definition"}
        server_definition = payload.get("server_definition")
        tool_name = _tool_name_from_activity(activity_name)

    if server_definition is None:
        raise ApplicationError(
            "MCP tool invocation is missing server_definition",
            type="MCPInvalidArgumentError",
            non_retryable=True,
        )

    return MCPToolInvocation(
        tool_name=tool_name,
        arguments=arguments,
        server_definition=server_definition,
    )


def _tool_name_from_activity(activity_name: str) -> str:
    parsed = parse_mcp_activity_name(activity_name)
    if parsed:
        return parsed["tool"]
    return activity_name


def _wrap_error(exc: BaseException) -> MCPToolError:
    """Convert a Python exception into a structured :class:`MCPToolError`."""
    error_type = type(exc).__name__
    return MCPToolError(
        message=str(exc),
        error_type=error_type,
        retryable=error_type not in NON_RETRYABLE_ERROR_TYPES,
    )


async def _call_via_pooled_manager(
    invocation: MCPToolInvocation,
) -> MCPToolResult:
    """Run the tool against the per-worker `MCPClientManager`, if available."""
    # Lazy import to avoid a hard dependency in unit tests that don't use it.
    from activities import mcp_dispatcher_registry  # noqa: WPS433

    manager = mcp_dispatcher_registry.get_client_manager()
    if manager is None:
        return await _call_via_one_shot(invocation)

    # Lazy local import keeps the module import-safe in workflow sandbox.
    from activities.tool_activities import _convert_args_types

    converted = _convert_args_types(invocation.arguments)
    client = await manager.get_client(invocation.server_definition)
    raw = await client.call_tool(invocation.tool_name, arguments=converted)

    # Lazy import for normalize helper.
    from activities.tool_activities import _normalize_result

    return MCPToolResult(
        tool=invocation.tool_name,
        success=True,
        content=_normalize_result(raw),
    )


async def _call_via_one_shot(invocation: MCPToolInvocation) -> MCPToolResult:
    """Fallback path that opens a fresh stdio connection per call."""
    from activities.tool_activities import _execute_mcp_tool

    legacy = await _execute_mcp_tool(
        invocation.tool_name,
        dict(invocation.arguments),
        invocation.server_definition,
    )
    if legacy.get("success"):
        return MCPToolResult(
            tool=invocation.tool_name,
            success=True,
            content=legacy.get("content"),
        )
    return MCPToolResult(
        tool=invocation.tool_name,
        success=False,
        error=MCPToolError(
            message=legacy.get("error", "Unknown MCP error"),
            error_type=legacy.get("error_type", "MCPError"),
            retryable=True,
        ),
    )


@activity.defn(dynamic=True)
async def mcp_tool_dispatcher(args: Sequence[RawValue]) -> Dict[str, Any]:
    """Dynamic dispatcher: one Temporal Activity boundary per MCP tool call.

    Returns a plain dict (the serialized form of :class:`MCPToolResult`) so
    workflows that already consume dict-shaped tool results keep working.
    Transport-level errors are re-raised as ``ApplicationError`` so Temporal's
    retry policy can re-attempt the call.
    """
    activity_name = activity.info().activity_type
    parsed = parse_mcp_activity_name(activity_name)

    # If this dispatcher was invoked for a non-MCP activity name, fall through
    # to the existing native-tool path so a single dispatcher can cover both.
    if parsed is None:
        return await _legacy_native_or_mcp_fallback(args, activity_name)

    payload_obj = activity.payload_converter().from_payload(args[0].payload, dict)
    try:
        invocation = _coerce_invocation(payload_obj, activity_name)
    except ApplicationError:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise ApplicationError(
            f"Could not coerce MCP invocation payload: {exc}",
            type="MCPInvalidArgumentError",
            non_retryable=True,
        ) from exc

    activity.logger.info(
        "Dispatching MCP tool '%s' on server '%s' (activity=%s)",
        invocation.tool_name,
        parsed["server"],
        activity_name,
    )

    try:
        result = await _call_via_pooled_manager(invocation)
    except ApplicationError:
        # Already shaped for Temporal's retry layer; let it propagate.
        raise
    except Exception as exc:
        # Transport / connection failures: let Temporal retry them.
        activity.logger.warning(
            "MCP tool '%s' raised %s; will be retried by Temporal RetryPolicy",
            invocation.tool_name,
            type(exc).__name__,
        )
        wrapped = _wrap_error(exc)
        raise ApplicationError(
            wrapped.message,
            type=wrapped.error_type,
            non_retryable=not wrapped.retryable,
        ) from exc

    return result.as_dict()


async def _legacy_native_or_mcp_fallback(
    args: Sequence[RawValue], activity_name: str
) -> Dict[str, Any]:
    """Mirror the prior `dynamic_tool_activity` behaviour for non-MCP names.

    Keeps the dispatcher usable as a drop-in replacement so a worker can
    register only this dispatcher (instead of the old dispatcher AND this
    one), simplifying configuration.
    """
    from tools import get_handler

    tool_args = activity.payload_converter().from_payload(args[0].payload, dict)
    activity.logger.info(
        "Dispatcher running non-MCP activity '%s' with args=%s",
        activity_name,
        tool_args,
    )

    server_definition = tool_args.pop("server_definition", None)
    if server_definition is not None:
        # Legacy MCP shape: forward to MCP path with the same arg layout.
        invocation = MCPToolInvocation(
            tool_name=activity_name,
            arguments=tool_args,
            server_definition=server_definition,
        )
        try:
            result = await _call_via_pooled_manager(invocation)
        except Exception as exc:
            wrapped = _wrap_error(exc)
            raise ApplicationError(
                wrapped.message,
                type=wrapped.error_type,
                non_retryable=not wrapped.retryable,
            ) from exc
        return result.as_dict()

    handler = get_handler(activity_name)
    if inspect.iscoroutinefunction(handler):
        result = await handler(tool_args)
    else:
        result = handler(tool_args)
    activity.logger.info("Native tool '%s' result: %s", activity_name, result)
    return result
