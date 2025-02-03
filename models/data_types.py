from dataclasses import dataclass
from typing import Optional, Deque, Dict, Any, List, Union, Literal
from models.tool_definitions import AgentGoal


@dataclass
class ToolWorkflowParams:
    conversation_summary: Optional[str] = None
    prompt_queue: Optional[Deque[str]] = None


@dataclass
class CombinedInput:
    tool_params: ToolWorkflowParams
    agent_goal: AgentGoal


Message = Dict[str, Union[str, Dict[str, Any]]]
ConversationHistory = Dict[str, List[Message]]
NextStep = Literal["confirm", "question", "done"]


@dataclass
class ToolPromptInput:
    prompt: str
    context_instructions: str


@dataclass
class ValidationInput:
    prompt: str
    conversation_history: ConversationHistory
    agent_goal: AgentGoal


@dataclass
class ValidationResult:
    validationResult: bool
    validationFailedReason: dict = None

    def __post_init__(self):
        # Initialize empty dict if None
        if self.validationFailedReason is None:
            self.validationFailedReason = {}
