import asyncio
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Dict, Tuple

from temporalio import activity

from models.tool_definitions import MCPServerDefinition

# Import MCP client libraries
if TYPE_CHECKING:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
else:
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError:
        # Fallback if MCP not installed
        ClientSession = None
        StdioServerParameters = None
        stdio_client = None


class MCPClientManager:
    """Manages pooled MCP client connections for reuse across tool calls"""

    def __init__(self):
        self._clients: Dict[str, Any] = {}
        self._connections: Dict[str, Tuple[Any, Any]] = {}
        self._lock = asyncio.Lock()

    async def get_client(
        self, server_def: MCPServerDefinition | Dict[str, Any] | None
    ) -> Any:
        """Return existing client or create new one, keyed by server definition hash"""
        async with self._lock:
            key = self._get_server_key(server_def)
            if key not in self._clients:
                await self._create_client(server_def, key)
                activity.logger.info(
                    f"Created new MCP client for {self._get_server_name(server_def)}"
                )
            else:
                activity.logger.info(
                    f"Reusing existing MCP client for {self._get_server_name(server_def)}"
                )
            return self._clients[key]

    def _get_server_key(
        self, server_def: MCPServerDefinition | Dict[str, Any] | None
    ) -> str:
        """Generate unique key for server definition"""
        if server_def is None:
            return "default:python:server.py"

        # Handle both MCPServerDefinition objects and dicts (from Temporal serialization)
        if isinstance(server_def, dict):
            name = server_def.get("name", "default")
            command = server_def.get("command", "python")
            args = server_def.get("args", ["server.py"])
        else:
            name = server_def.name
            command = server_def.command
            args = server_def.args

        return f"{name}:{command}:{':'.join(args)}"

    def _get_server_name(
        self, server_def: MCPServerDefinition | Dict[str, Any] | None
    ) -> str:
        """Get server name for logging"""
        if server_def is None:
            return "default"

        if isinstance(server_def, dict):
            return server_def.get("name", "default")
        else:
            return server_def.name

    def _build_connection(
        self, server_def: MCPServerDefinition | Dict[str, Any] | None
    ) -> Dict[str, Any]:
        """Build connection parameters from MCPServerDefinition or dict"""
        if server_def is None:
            # Default to stdio connection with the main server
            return {
                "type": "stdio",
                "command": "python",
                "args": ["server.py"],
                "env": {},
            }

        # Handle both MCPServerDefinition objects and dicts (from Temporal serialization)
        if isinstance(server_def, dict):
            return {
                "type": server_def.get("connection_type", "stdio"),
                "command": server_def.get("command", "python"),
                "args": server_def.get("args", ["server.py"]),
                "env": server_def.get("env", {}) or {},
            }

        return {
            "type": server_def.connection_type,
            "command": server_def.command,
            "args": server_def.args,
            "env": server_def.env or {},
        }

    @asynccontextmanager
    async def _stdio_connection(self, command: str, args: list, env: dict):
        """Create stdio connection to MCP server"""
        if stdio_client is None:
            raise Exception("MCP client libraries not available")

        # Create server parameters
        server_params = StdioServerParameters(command=command, args=args, env=env)

        async with stdio_client(server_params) as (read, write):
            yield read, write

    async def _create_client(
        self, server_def: MCPServerDefinition | Dict[str, Any] | None, key: str
    ):
        """Create and store new client connection"""
        connection = self._build_connection(server_def)

        if connection["type"] == "stdio":
            # Create stdio connection
            connection_manager = self._stdio_connection(
                command=connection.get("command", "python"),
                args=connection.get("args", ["server.py"]),
                env=connection.get("env", {}),
            )

            # Enter the connection context
            read, write = await connection_manager.__aenter__()

            # Create and initialize client session
            session = ClientSession(read, write)
            await session.initialize()

            # Store both the session and connection manager for cleanup
            self._clients[key] = session
            self._connections[key] = (connection_manager, read, write)
        else:
            raise Exception(f"Unsupported connection type: {connection['type']}")

    async def cleanup(self):
        """Close all connections gracefully"""
        async with self._lock:
            # Close all client sessions
            for session in self._clients.values():
                try:
                    await session.close()
                except Exception as e:
                    activity.logger.warning(f"Error closing MCP session: {e}")

            # Exit all connection contexts
            for connection_manager, read, write in self._connections.values():
                try:
                    await connection_manager.__aexit__(None, None, None)
                except Exception as e:
                    activity.logger.warning(f"Error closing MCP connection: {e}")

            self._clients.clear()
            self._connections.clear()
            activity.logger.info("All MCP connections closed")
