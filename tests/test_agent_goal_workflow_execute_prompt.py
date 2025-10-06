import pytest

from models.data_types import ToolPromptInput
from models.tool_definitions import AgentGoal, ToolDefinition, ToolArgument
import workflows.agent_goal_workflow as agw_module


@pytest.mark.asyncio
async def test__execute_prompt_success(monkeypatch):
    """
    Test that _execute_prompt calls execute_activity_method as expected
    """
    # Arrange: create workflow instance and set a concrete goal
    wf = agw_module.AgentGoalWorkflow()
    wf.fallback_mode = False
    wf.goal = AgentGoal(
        id="unit_goal_id",
        category_tag="unit_cat",
        agent_name="UnitAgent",
        agent_friendly_description="Unit test agent",
        description="Unit test goal description",
        tools=[
            ToolDefinition(
                name="UnitTool",
                description="Unit tool",
                arguments=[ToolArgument(name="param", type="string", description="p")],
            )
        ],
    )

    # Capture container
    captured = {"activity_called": False}

    # Create a minimal workflow mock exposing only execute_activity_method
    class WorkflowMock:
        async def execute_activity_method(self, activity, *, args, schedule_to_close_timeout, start_to_close_timeout, retry_policy, summary):
            captured["activity_called"] = True

            # Validate args structure and values
            assert isinstance(args, list)
            assert len(args) == 2
            prompt_input, fallback_mode = args
            assert isinstance(prompt_input, ToolPromptInput)
            assert prompt_input.prompt == "test prompt"
            assert prompt_input.context_instructions == "test context"
            assert fallback_mode is False

            # Validate timeouts and retry policy were forwarded
            assert schedule_to_close_timeout == agw_module.LLM_ACTIVITY_SCHEDULE_TO_CLOSE_TIMEOUT
            assert start_to_close_timeout == agw_module.LLM_ACTIVITY_START_TO_CLOSE_TIMEOUT
            # Retry policy values as defined in workflow implementation
            assert retry_policy.initial_interval.total_seconds() == 5
            assert retry_policy.backoff_coefficient == 1
            assert retry_policy.maximum_attempts == 2

            # Summary should be empty when not in fallback
            assert summary == ""

            # Return a successful tool_data response
            return {
                "next": "confirm",
                "tool": "UnitTool",
                "args": {"param": "value"},
                "response": "Tool response"
            }

    # Monkeypatch the module-level `workflow` object to our minimal mock
    monkeypatch.setattr(agw_module, "workflow", WorkflowMock(), raising=True)

    # Create prompt input
    prompt_input = ToolPromptInput(
        prompt="test prompt",
        context_instructions="test context"
    )

    # Act
    result = await wf._execute_prompt(prompt_input)

    # Assert
    assert captured["activity_called"] is True
    assert isinstance(result, dict)
    assert result["next"] == "confirm"
    assert result["tool"] == "UnitTool"
    assert result["args"] == {"param": "value"}
    assert result["response"] == "Tool response"


@pytest.mark.asyncio
async def test__execute_prompt_activityerror_triggers_fallback(monkeypatch):
    """
    Test that _execute_prompt handles the ActivityError by calling the fallback.
    """
    # Arrange
    wf = agw_module.AgentGoalWorkflow()
    wf.fallback_mode = False
    wf.goal = AgentGoal(
        id="unit_goal_id_2",
        category_tag="unit_cat",
        agent_name="UnitAgent",
        agent_friendly_description="Unit test agent",
        description="Unit test goal description",
        tools=[
            ToolDefinition(
                name="UnitTool",
                description="Unit tool",
                arguments=[ToolArgument(name="param", type="string", description="p")],
            )
        ],
    )

    calls = {"count": 0}

    from temporalio.exceptions import ActivityError
    from temporalio.api.enums.v1 import RetryState

    class WorkflowMock:
        class _Logger:
            def info(self, *args, **kwargs):
                return None

        logger = _Logger()
        async def execute_activity_method(self, activity, *, args, schedule_to_close_timeout, start_to_close_timeout, retry_policy, summary):
            calls["count"] += 1
            prompt_input, fallback_mode = args
            if calls["count"] == 1:
                # First attempt should be non-fallback and raise ActivityError
                assert fallback_mode is False
                assert summary == ""
                raise ActivityError(
                    message="primary failure",
                    scheduled_event_id=1,
                    started_event_id=2,
                    identity="unit-test",
                    activity_type="agent_tool_planner",
                    activity_id="activity-1",
                    retry_state=RetryState.RETRY_STATE_MAXIMUM_ATTEMPTS_REACHED,
                )

            # Second attempt should be fallback
            assert fallback_mode is True
            assert summary == "fallback"
            assert prompt_input.prompt == "test prompt"
            assert prompt_input.context_instructions == "test context"

            # Validate timeouts and retry policy forwarded
            assert schedule_to_close_timeout == agw_module.LLM_ACTIVITY_SCHEDULE_TO_CLOSE_TIMEOUT
            assert start_to_close_timeout == agw_module.LLM_ACTIVITY_START_TO_CLOSE_TIMEOUT
            assert retry_policy.initial_interval.total_seconds() == 5
            assert retry_policy.backoff_coefficient == 1
            assert retry_policy.maximum_attempts == 2

            return {
                "next": "confirm",
                "tool": "UnitTool",
                "args": {"param": "value"},
                "response": "Fallback tool response"
            }

    monkeypatch.setattr(agw_module, "workflow", WorkflowMock(), raising=True)

    # Create prompt input
    prompt_input = ToolPromptInput(
        prompt="test prompt",
        context_instructions="test context"
    )

    # Act
    result = await wf._execute_prompt(prompt_input)

    # Assert
    assert isinstance(result, dict)
    assert result["next"] == "confirm"
    assert result["response"] == "Fallback tool response"
    assert wf.fallback_mode is True
    assert calls["count"] == 2