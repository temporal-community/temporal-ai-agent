from dataclasses import dataclass, field
from typing import List, Dict, Any


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
class ToolsData:
    tools: List[ToolDefinition]
