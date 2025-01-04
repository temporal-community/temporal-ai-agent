from dataclasses import dataclass
from typing import List


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
    tools: List[ToolDefinition]
    description: str = "Description of the tools purpose and overall goal"
    example_conversation_history: str = (
        "Example conversation history to help the AI agent understand the context of the conversation"
    )
