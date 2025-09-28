from datetime import timedelta
from typing import Any, Deque, Dict

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError

from models.data_types import ConversationHistory, ToolPromptInput
from models.tool_definitions import AgentGoal, ToolDefinition
from prompts.agent_prompt_generators import (
    generate_missing_args_prompt,
    generate_tool_completion_prompt,
)
from shared.config import TEMPORAL_LEGACY_TASK_QUEUE

# Constants from original file
TOOL_ACTIVITY_START_TO_CLOSE_TIMEOUT = timedelta(seconds=12)
TOOL_ACTIVITY_SCHEDULE_TO_CLOSE_TIMEOUT = timedelta(minutes=30)
LLM_ACTIVITY_START_TO_CLOSE_TIMEOUT = timedelta(seconds=20)
LLM_ACTIVITY_SCHEDULE_TO_CLOSE_TIMEOUT = timedelta(minutes=30)


def is_mcp_tool(tool_name: str, goal: AgentGoal) -> bool:
    """Check if a tool should be dispatched via MCP."""
    if not goal.mcp_server_definition:
        return False

    # Native tools are registered with tools.get_handler. If lookup succeeds,
    # the tool should execute locally; otherwise treat it as MCP-provided.
    from tools import get_handler

    try:
        get_handler(tool_name)
        return False
    except ValueError:
        return True


async def handle_tool_execution(
    current_tool: str,
    tool_data: Dict[str, Any],
    tool_results: list,
    add_message_callback: callable,
    prompt_queue: Deque[str],
    goal: AgentGoal = None,
) -> None:
    """Execute a tool after confirmation and handle its result."""
    workflow.logger.info(f"Confirmed. Proceeding with tool: {current_tool}")

    try:
        # Check if this is an MCP tool
        if goal and is_mcp_tool(current_tool, goal):
            workflow.logger.info(f"Executing MCP tool: {current_tool}")

            # Add server definition to args for MCP tools
            mcp_args = tool_data["args"].copy()

            # Stripe's MCP server enforces days_until_due when the collection
            # method defaults to send_invoice. Provide a reasonable default when
            # the planner omits it so invoice creation doesn't fail upstream.
            if current_tool == "create_invoice" and "days_until_due" not in mcp_args:
                mcp_args["days_until_due"] = 7

            mcp_args["server_definition"] = goal.mcp_server_definition

            dynamic_result = await workflow.execute_activity(
                current_tool,
                mcp_args,
                schedule_to_close_timeout=TOOL_ACTIVITY_SCHEDULE_TO_CLOSE_TIMEOUT,
                start_to_close_timeout=TOOL_ACTIVITY_START_TO_CLOSE_TIMEOUT,
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=5), backoff_coefficient=1
                ),
                summary=f"{goal.mcp_server_definition.name} (MCP Tool)",
            )
        else:
            # Handle regular tools
            task_queue = (
                TEMPORAL_LEGACY_TASK_QUEUE
                if current_tool in ["SearchTrains", "BookTrains"]
                else None
            )

            dynamic_result = await workflow.execute_activity(
                current_tool,
                tool_data["args"],
                task_queue=task_queue,
                schedule_to_close_timeout=TOOL_ACTIVITY_SCHEDULE_TO_CLOSE_TIMEOUT,
                start_to_close_timeout=TOOL_ACTIVITY_START_TO_CLOSE_TIMEOUT,
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=5), backoff_coefficient=1
                ),
            )

        dynamic_result["tool"] = current_tool
        tool_results.append(dynamic_result)

    except ActivityError as e:
        workflow.logger.error(f"Tool execution failed: {str(e)}")
        dynamic_result = {"error": str(e), "tool": current_tool}

    add_message_callback("tool_result", dynamic_result)
    prompt_queue.append(generate_tool_completion_prompt(current_tool, dynamic_result))


async def handle_missing_args(
    current_tool: str,
    args: Dict[str, Any],
    tool_data: Dict[str, Any],
    prompt_queue: Deque[str],
) -> bool:
    """Check for missing arguments and handle them if found."""
    missing_args = [key for key, value in args.items() if value is None]

    if missing_args:
        prompt_queue.append(
            generate_missing_args_prompt(current_tool, tool_data, missing_args)
        )
        workflow.logger.info(
            f"Missing arguments for tool: {current_tool}: {' '.join(missing_args)}"
        )
        return True
    return False


def format_history(conversation_history: ConversationHistory) -> str:
    """Format the conversation history into a single string."""
    return " ".join(str(msg["response"]) for msg in conversation_history["messages"])


def prompt_with_history(
    conversation_history: ConversationHistory, prompt: str
) -> tuple[str, str]:
    """Generate a context-aware prompt with conversation history."""
    history_string = format_history(conversation_history)
    context_instructions = (
        f"Here is the conversation history: {history_string} "
        "Please add a few sentence response in plain text sentences. "
        "Don't editorialize or add metadata. "
        "Keep the text a plain explanation based on the history."
    )
    return (context_instructions, prompt)


async def continue_as_new_if_needed(
    conversation_history: ConversationHistory,
    prompt_queue: Deque[str],
    agent_goal: Any,
    max_turns: int,
    add_message_callback: callable,
) -> None:
    """Handle workflow continuation if message limit is reached."""
    if len(conversation_history["messages"]) >= max_turns:
        summary_context, summary_prompt = prompt_summary_with_history(
            conversation_history
        )
        summary_input = ToolPromptInput(
            prompt=summary_prompt, context_instructions=summary_context
        )
        conversation_summary = await workflow.start_activity_method(
            "ToolActivities.agent_toolPlanner",
            summary_input,
            schedule_to_close_timeout=LLM_ACTIVITY_SCHEDULE_TO_CLOSE_TIMEOUT,
        )
        workflow.logger.info(f"Continuing as new after {max_turns} turns.")
        add_message_callback("conversation_summary", conversation_summary)
        workflow.continue_as_new(
            args=[
                {
                    "tool_params": {
                        "conversation_summary": conversation_summary,
                        "prompt_queue": prompt_queue,
                    },
                    "agent_goal": agent_goal,
                }
            ]
        )


def prompt_summary_with_history(
    conversation_history: ConversationHistory,
) -> tuple[str, str]:
    """Generate a prompt for summarizing the conversation.
    Used only for continue as new of the workflow."""
    history_string = format_history(conversation_history)
    context_instructions = f"Here is the conversation history between a user and a chatbot: {history_string}"
    actual_prompt = (
        "Please produce a two sentence summary of this conversation. "
        'Put the summary in the format { "summary": "<plain text>" }'
    )
    return (context_instructions, actual_prompt)
