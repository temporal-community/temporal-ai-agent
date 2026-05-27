"""Process-wide registry for the MCP dispatcher's pooled client manager.

The dispatcher is a free function (because it must be a top-level
`@activity.defn(dynamic=True)`), so it can't capture a `self.mcp_client_manager`
the way `ToolActivities` does. We bridge the gap with a tiny module-level
slot that the worker sets at startup.
"""

from __future__ import annotations

from typing import Optional

from shared.mcp_client_manager import MCPClientManager

_manager: Optional[MCPClientManager] = None


def set_client_manager(manager: Optional[MCPClientManager]) -> None:
    global _manager
    _manager = manager


def get_client_manager() -> Optional[MCPClientManager]:
    return _manager
