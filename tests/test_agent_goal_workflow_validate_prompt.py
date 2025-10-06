import pytest

from models.data_types import ValidationInput, ValidationResult
from models.tool_definitions import AgentGoal, ToolDefinition, ToolArgument
import workflows.agent_goal_workflow as agw_module


@pytest.mark.asyncio
async def test__validate_prompt_success(monkeypatch):
    """
    Test that _validate_prompt calls execute_activity_method as expected
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
    captured = {"add_message_called": False, "activity_called": False}

    # Mock add_message on the instance
    def fake_add_message(actor, response):
        captured["add_message_called"] = True
        assert actor == "user"
        assert response == "unit_prompt"

    monkeypatch.setattr(wf, "add_message", fake_add_message, raising=True)

    # Create a minimal workflow mock exposing only execute_activity_method
    class WorkflowMock:
        async def execute_activity_method(self, activity, *, args, schedule_to_close_timeout, start_to_close_timeout, retry_policy, summary):
            captured["activity_called"] = True

            # Validate args structure and values
            assert isinstance(args, list)
            assert len(args) == 2
            validation_input, fallback_mode = args
            assert isinstance(validation_input, ValidationInput)
            assert validation_input.prompt == "unit_prompt"
            assert validation_input.agent_goal.id == "unit_goal_id"
            assert isinstance(validation_input.conversation_history, dict)
            assert "messages" in validation_input.conversation_history
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

            # Return a successful ValidationResult
            return ValidationResult(validationResult=True, validationFailedReason={})

    # Monkeypatch the module-level `workflow` object to our minimal mock
    monkeypatch.setattr(agw_module, "workflow", WorkflowMock(), raising=True)

    # Act
    result = await wf._validate_prompt("unit_prompt")

    # Assert
    assert captured["add_message_called"] is True
    assert captured["activity_called"] is True
    assert isinstance(result, ValidationResult)
    assert result.validationResult is True


@pytest.mark.asyncio
async def test__validate_prompt_activityerror_triggers_fallback(monkeypatch):
    """
    Test that _validate_prompt handles the ActivityError by calling the fallback.
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

    # Ensure add_message still works but we don't assert twice here
    def fake_add_message(actor, response):
        assert actor == "user"
        assert response == "needs_fallback"

    monkeypatch.setattr(wf, "add_message", fake_add_message, raising=True)

    from temporalio.exceptions import ActivityError
    from temporalio.api.enums.v1 import RetryState

    class WorkflowMock:
        class _Logger:
            def info(self, *args, **kwargs):
                return None

        logger = _Logger()
        async def execute_activity_method(self, activity, *, args, schedule_to_close_timeout, start_to_close_timeout, retry_policy, summary):
            calls["count"] += 1
            validation_input, fallback_mode = args
            if calls["count"] == 1:
                # First attempt should be non-fallback and raise ActivityError
                assert fallback_mode is False
                assert summary == ""
                raise ActivityError(
                    message="primary failure",
                    scheduled_event_id=1,
                    started_event_id=2,
                    identity="unit-test",
                    activity_type="agent_validate_prompt",
                    activity_id="activity-1",
                    retry_state=RetryState.RETRY_STATE_MAXIMUM_ATTEMPTS_REACHED,
                )

            # Second attempt should be fallback
            assert fallback_mode is True
            assert summary == "fallback"
            assert validation_input.prompt == "needs_fallback"
            assert validation_input.agent_goal.id == "unit_goal_id_2"

            # Validate timeouts and retry policy forwarded
            assert schedule_to_close_timeout == agw_module.LLM_ACTIVITY_SCHEDULE_TO_CLOSE_TIMEOUT
            assert start_to_close_timeout == agw_module.LLM_ACTIVITY_START_TO_CLOSE_TIMEOUT
            assert retry_policy.initial_interval.total_seconds() == 5
            assert retry_policy.backoff_coefficient == 1
            assert retry_policy.maximum_attempts == 2

            return ValidationResult(validationResult=True, validationFailedReason={})

    monkeypatch.setattr(agw_module, "workflow", WorkflowMock(), raising=True)

    # Act
    result = await wf._validate_prompt("needs_fallback")

    # Assert
    assert isinstance(result, ValidationResult)
    assert result.validationResult is True
    assert wf.fallback_mode is True
    assert calls["count"] == 2
