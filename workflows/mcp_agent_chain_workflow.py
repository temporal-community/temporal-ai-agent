"""Sample workflow: a durable multi-tool MCP agent chain.

This workflow takes a sequence of MCP tool invocations selected by an upstream
LLM and executes each one through the typed dispatcher activity. It exists to
show how to wire arbitrary, LLM-chosen MCP tools to dedicated Temporal
Activity boundaries with:

* state persistence — every step's input and result lives in workflow
  history, and a workflow query exposes the running list of results,
* automatic retries — Temporal's RetryPolicy retries transient MCP failures
  at the activity boundary, with non-retryable error types bypassing retry,
* structured error handling — failures become typed `MCPToolResult` objects
  so the chain can continue, stop, or branch based on the error.

The workflow is intentionally minimal: it doesn't call the LLM itself. In
production you'd interleave dispatcher calls with LLM planning steps; the
shape stays the same.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from models.mcp_types import MCPToolInvocation, MCPToolResult
    from workflows.mcp_dispatcher_helpers import invoke_mcp_tool


@dataclass
class MCPAgentChainInput:
    """Input bundle for the sample chain workflow."""

    invocations: List[MCPToolInvocation]
    # If True, stop the chain on the first failure. If False, continue and
    # collect every result.
    stop_on_failure: bool = True


@dataclass
class MCPAgentChainOutput:
    results: List[Dict[str, Any]] = field(default_factory=list)
    completed: int = 0
    failed: int = 0


@workflow.defn
class MCPAgentChainWorkflow:
    """Execute a chain of MCP tool calls as one durable Temporal Workflow."""

    def __init__(self) -> None:
        self._results: List[MCPToolResult] = []
        self._completed: int = 0
        self._failed: int = 0
        self._current_tool: Optional[str] = None

    @workflow.run
    async def run(self, chain_input: MCPAgentChainInput) -> MCPAgentChainOutput:
        for invocation in chain_input.invocations:
            self._current_tool = invocation.tool_name
            workflow.logger.info(
                "MCPAgentChain: executing tool %s (%d/%d)",
                invocation.tool_name,
                self._completed + self._failed + 1,
                len(chain_input.invocations),
            )

            result = await invoke_mcp_tool(
                tool_name=invocation.tool_name,
                arguments=invocation.arguments,
                server_definition=invocation.server_definition,
                summary=invocation.summary,
            )

            self._results.append(result)
            if result.success:
                self._completed += 1
            else:
                self._failed += 1
                workflow.logger.warning(
                    "MCPAgentChain: tool %s failed (%s)",
                    invocation.tool_name,
                    result.error.error_type if result.error else "unknown",
                )
                if chain_input.stop_on_failure:
                    break

        self._current_tool = None
        return MCPAgentChainOutput(
            results=[r.as_dict() for r in self._results],
            completed=self._completed,
            failed=self._failed,
        )

    @workflow.query
    def get_results(self) -> List[Dict[str, Any]]:
        """Return the list of MCP tool results gathered so far."""
        return [r.as_dict() for r in self._results]

    @workflow.query
    def get_current_tool(self) -> Optional[str]:
        """Return the name of the tool currently executing (if any)."""
        return self._current_tool
