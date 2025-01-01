from dataclasses import dataclass
from typing import Optional, Deque
from models.tool_definitions import ToolsData


@dataclass
class ToolWorkflowParams:
    conversation_summary: Optional[str] = None
    prompt_queue: Optional[Deque[str]] = None


@dataclass
class CombinedInput:
    tool_params: ToolWorkflowParams
    tools_data: ToolsData
