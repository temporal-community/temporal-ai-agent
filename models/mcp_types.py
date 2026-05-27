"""Typed data structures for the MCP-to-Temporal-Activity dispatcher.

These types let workflows and activities exchange MCP tool invocations and
results as well-defined dataclasses (instead of bare dicts), so that:

* Temporal history records contain structured, serializable input/output for
  every MCP tool call.
* Workflow code can branch on a single `success` flag and a typed error,
  instead of inspecting ad-hoc dict keys.
* Failures keep enough context to retry, surface to the LLM, or fail cleanly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union

from models.tool_definitions import MCPServerDefinition


@dataclass
class MCPToolInvocation:
    """A single MCP tool call routed through the dispatcher activity.

    `server_definition` is required so the dispatcher activity can route to
    the correct MCP server without relying on global state.
    """

    tool_name: str
    arguments: Dict[str, Any]
    server_definition: Union[MCPServerDefinition, Dict[str, Any]]
    # Optional, human-friendly label used in Temporal UI for the activity.
    summary: Optional[str] = None


@dataclass
class MCPToolError:
    """Structured error captured when an MCP tool call fails.

    `retryable` lets workflow code decide whether to plan another attempt at
    the LLM/agent level (Temporal's RetryPolicy handles transport-level
    retries automatically before this is returned).
    """

    message: str
    error_type: str
    retryable: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPToolResult:
    """Result of dispatching an MCP tool invocation as a Temporal Activity.

    A successful invocation populates `content`. A failed one populates
    `error` and leaves `content` empty. Workflows can chain on `success`.
    """

    tool: str
    success: bool
    content: Any = None
    error: Optional[MCPToolError] = None

    def as_dict(self) -> Dict[str, Any]:
        """Convert to a plain dict for legacy code paths that expect one."""
        out: Dict[str, Any] = {"tool": self.tool, "success": self.success}
        if self.content is not None:
            out["content"] = self.content
        if self.error is not None:
            out["error"] = self.error.message
            out["error_type"] = self.error.error_type
            out["retryable"] = self.error.retryable
            if self.error.details:
                out["error_details"] = self.error.details
        return out
