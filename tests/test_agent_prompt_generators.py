import uuid

from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker

import tools.tool_registry as tool_registry
from goals.ecommerce import goal_ecomm_order_status
from goals.hr import goal_hr_schedule_pto
from models.data_types import (
    CombinedInput,
    EnvLookupInput,
    EnvLookupOutput,
    ToolPromptInput,
    ValidationInput,
    ValidationResult,
)
from prompts.agent_prompt_generators import (
    generate_genai_prompt,
    generate_tool_completion_prompt,
)
from workflows.agent_goal_workflow import AgentGoalWorkflow

HISTORY = {
    "messages": [
        {"actor": "user", "response": "I'd like to schedule some time off"},
        {
            "actor": "agent",
            "response": {
                "next": "question",
                "tool": None,
                "args": {},
                "response": "May I have your email address?",
            },
        },
    ]
}


def _prompt(goal) -> str:
    return generate_genai_prompt(
        agent_goal=goal, conversation_history=HISTORY, multi_goal_mode=False
    )


def test_planner_prompt_has_no_rules_for_tools_of_other_goals():
    prompt = _prompt(goal_hr_schedule_pto)
    for text in ["list_prices", "create_invoice_item", "pizza", "EXAMPLES:"]:
        assert text not in prompt


def test_planner_prompt_has_no_keyword_cues():
    prompt = _prompt(goal_ecomm_order_status)
    assert "let's get/proceed/check" not in prompt
    assert "completion indicators" not in prompt


def test_planner_prompt_states_json_only_rule_once():
    prompt = _prompt(goal_ecomm_order_status)
    for text in [
        "CRITICAL: You must respond with ONLY valid JSON",
        "JSON-ONLY RESPONSE FORMAT",
        "MANDATORY:",
        "RESPOND WITH JSON ONLY",
        "FINAL REMINDER",
        "RESPOND WITH VALID JSON ONLY",
    ]:
        assert text not in prompt
    assert prompt.count("Required JSON format:") == 1
    assert prompt.count("Return ONLY a valid JSON response.") == 1


def test_tool_completion_prompt_does_not_force_question_between_tools():
    prompt = generate_tool_completion_prompt("GetOrder", {"status": "shipped"})
    assert "if the tool is not the last one in the sequence" not in prompt


def _arg_names(tool) -> list:
    return [arg.name for arg in tool.arguments]


def test_read_only_tools_have_no_user_confirmation_arg():
    for tool in [tool_registry.search_flights_tool, tool_registry.ecomm_track_package]:
        assert "userConfirmation" not in _arg_names(tool), tool.name


def test_state_changing_tools_keep_user_confirmation_arg():
    for tool in [
        tool_registry.book_trains_tool,
        tool_registry.create_invoice_tool,
        tool_registry.book_pto_tool,
        tool_registry.financial_move_money,
    ]:
        assert "userConfirmation" in _arg_names(tool), tool.name


async def test_second_turn_planner_prompt_has_no_validation_task(
    client: Client, sample_combined_input: CombinedInput
):
    """From the second turn on, the planner prompt must not ask the model to
    validate its own previous output."""
    task_queue_name = str(uuid.uuid4())
    planner_prompts: list = []

    @activity.defn(name="get_wf_env_vars")
    async def mock_get_wf_env_vars(input: EnvLookupInput) -> EnvLookupOutput:
        return EnvLookupOutput(show_confirm=True, multi_goal_mode=False)

    @activity.defn(name="agent_validatePrompt")
    async def mock_agent_validatePrompt(
        validation_input: ValidationInput,
    ) -> ValidationResult:
        return ValidationResult(validationResult=True, validationFailedReason={})

    @activity.defn(name="agent_toolPlanner")
    async def mock_agent_toolPlanner(input: ToolPromptInput) -> dict:
        planner_prompts.append(input.context_instructions)
        if len(planner_prompts) == 1:
            return {
                "next": "question",
                "tool": None,
                "args": {},
                "response": "What is your test_arg?",
            }
        return {"next": "done", "tool": None, "args": {}, "response": "Bye"}

    async with Worker(
        client,
        task_queue=task_queue_name,
        workflows=[AgentGoalWorkflow],
        activities=[
            mock_get_wf_env_vars,
            mock_agent_validatePrompt,
            mock_agent_toolPlanner,
        ],
    ):
        handle = await client.start_workflow(
            AgentGoalWorkflow.run,
            sample_combined_input,
            id=str(uuid.uuid4()),
            task_queue=task_queue_name,
        )
        await handle.signal(AgentGoalWorkflow.user_prompt, "hello")
        await handle.signal(AgentGoalWorkflow.user_prompt, "my test_arg is 42")
        await handle.result()

    assert len(planner_prompts) == 2
    second = planner_prompts[1]
    assert "Validation Task" not in second
    assert "Validate the provided JSON" not in second
    assert "What is your test_arg?" in second  # still sees the previous turn
