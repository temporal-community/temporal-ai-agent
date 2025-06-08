from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class MCPServerDefinition:
    """Definition for an MCP (Model Context Protocol) server connection"""
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None
    connection_type: str = "stdio"
    included_tools: Optional[List[str]] = None


@dataclass
class ToolArgument:
    name: str
    type: str
    description: str


@dataclass
class ToolDefinition:
    name: str
    description: str
    arguments: List[ToolArgument]


@dataclass
class AgentGoal:
    id: str
    category_tag: str
    agent_name: str
    agent_friendly_description: str
    tools: List[ToolDefinition]
    description: str = "Description of the tools purpose and overall goal"
    starter_prompt: str = "Initial prompt to start the conversation"
    example_conversation_history: str = "Example conversation history to help the AI agent understand the context of the conversation"
    mcp_server_definition: Optional[MCPServerDefinition] = None
