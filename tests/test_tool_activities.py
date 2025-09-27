import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from temporalio.client import Client
from temporalio.testing import ActivityEnvironment

from activities.tool_activities import (
    MCPServerDefinition,
    ToolActivities,
    dynamic_tool_activity,
)
from models.data_types import (
    EnvLookupInput,
    EnvLookupOutput,
    ToolPromptInput,
    ValidationInput,
    ValidationResult,
)


class TestToolActivities:
    """Test cases for ToolActivities."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.tool_activities = ToolActivities()

    @pytest.mark.asyncio
    async def test_agent_validatePrompt_valid_prompt(
        self, sample_agent_goal, sample_conversation_history
    ):
        """Test agent_validatePrompt with a valid prompt."""
        validation_input = ValidationInput(
            prompt="I need help with the test tool",
            conversation_history=sample_conversation_history,
            agent_goal=sample_agent_goal,
        )

        # Mock the agent_tool_planner to return a valid response
        mock_response = {"validationResult": True, "validationFailedReason": {}}

        with patch.object(
            self.tool_activities, "agent_tool_planner", new_callable=AsyncMock
        ) as mock_planner:
            mock_planner.return_value = mock_response

            activity_env = ActivityEnvironment()
            result = await activity_env.run(
                self.tool_activities.agent_validatePrompt, validation_input
            )

            assert isinstance(result, ValidationResult)
            assert result.validationResult is True
            assert result.validationFailedReason == {}

            # Verify the mock was called with correct parameters
            mock_planner.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_validatePrompt_invalid_prompt(
        self, sample_agent_goal, sample_conversation_history
    ):
        """Test agent_validatePrompt with an invalid prompt."""
        validation_input = ValidationInput(
            prompt="asdfghjkl nonsense",
            conversation_history=sample_conversation_history,
            agent_goal=sample_agent_goal,
        )

        # Mock the agent_tool_planner to return an invalid response
        mock_response = {
            "validationResult": False,
            "validationFailedReason": {
                "next": "question",
                "response": "Your request doesn't make sense in this context",
            },
        }

        with patch.object(
            self.tool_activities, "agent_tool_planner", new_callable=AsyncMock
        ) as mock_planner:
            mock_planner.return_value = mock_response

            activity_env = ActivityEnvironment()
            result = await activity_env.run(
                self.tool_activities.agent_validatePrompt, validation_input
            )

            assert isinstance(result, ValidationResult)
            assert result.validationResult is False
            assert "doesn't make sense" in str(result.validationFailedReason)

    @pytest.mark.asyncio
    async def test_agent_tool_planner_success(self):
        """Test agent_tool_planner with successful LLM response."""
        prompt_input = ToolPromptInput(
            prompt="Test prompt", context_instructions="Test context instructions"
        )

        # Mock the llm_manager.call_llm method
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = (
            '{"next": "confirm", "tool": "TestTool", "response": "Test response"}'
        )

        with patch.object(
            self.tool_activities.llm_manager, "call_llm", new_callable=AsyncMock
        ) as mock_call_llm:
            mock_call_llm.return_value = mock_response

            activity_env = ActivityEnvironment()
            result = await activity_env.run(
                self.tool_activities.agent_tool_planner, prompt_input
            )

            assert isinstance(result, dict)
            assert result["next"] == "confirm"
            assert result["tool"] == "TestTool"
            assert result["response"] == "Test response"

            # Verify call_llm was called with correct parameters
            mock_call_llm.assert_called_once()
            call_args = mock_call_llm.call_args[0][
                0
            ]  # First positional argument (messages)
            assert len(call_args) == 2
            assert call_args[0]["role"] == "system"
            assert call_args[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_agent_tool_planner_with_custom_base_url(self):
        """Test agent_tool_planner with custom base URL configuration."""
        # Set up tool activities with custom base URL
        with patch.dict(os.environ, {"LLM_BASE_URL": "https://custom.endpoint.com"}):
            tool_activities = ToolActivities()

            prompt_input = ToolPromptInput(
                prompt="Test prompt", context_instructions="Test context instructions"
            )

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[
                0
            ].message.content = '{"next": "done", "response": "Test"}'

            with patch.object(
                tool_activities.llm_manager, "call_llm", new_callable=AsyncMock
            ) as mock_call_llm:
                mock_call_llm.return_value = mock_response

                activity_env = ActivityEnvironment()
                await activity_env.run(tool_activities.agent_tool_planner, prompt_input)

                # Verify call_llm was called
                mock_call_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_tool_planner_json_parsing_error(self):
        """Test agent_tool_planner handles JSON parsing errors."""
        prompt_input = ToolPromptInput(
            prompt="Test prompt", context_instructions="Test context instructions"
        )

        # Mock the llm_manager.call_llm method to return invalid JSON
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Invalid JSON response"

        with patch.object(
            self.tool_activities.llm_manager, "call_llm", new_callable=AsyncMock
        ) as mock_call_llm:
            mock_call_llm.return_value = mock_response

            activity_env = ActivityEnvironment()
            with pytest.raises(Exception):  # Should raise JSON parsing error
                await activity_env.run(
                    self.tool_activities.agent_tool_planner, prompt_input
                )

    @pytest.mark.asyncio
    async def test_get_wf_env_vars_default_values(self):
        """Test get_wf_env_vars with default values."""
        env_input = EnvLookupInput(
            show_confirm_env_var_name="SHOW_CONFIRM", show_confirm_default=True
        )

        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            activity_env = ActivityEnvironment()
            result = await activity_env.run(
                self.tool_activities.get_wf_env_vars, env_input
            )

            assert isinstance(result, EnvLookupOutput)
            assert result.show_confirm is True  # default value
            assert result.multi_goal_mode is False  # default value (single agent mode)

    @pytest.mark.asyncio
    async def test_get_wf_env_vars_custom_values(self):
        """Test get_wf_env_vars with custom environment values."""
        env_input = EnvLookupInput(
            show_confirm_env_var_name="SHOW_CONFIRM", show_confirm_default=True
        )

        # Set environment variables
        with patch.dict(
            os.environ, {"SHOW_CONFIRM": "false", "AGENT_GOAL": "specific_goal"}
        ):
            activity_env = ActivityEnvironment()
            result = await activity_env.run(
                self.tool_activities.get_wf_env_vars, env_input
            )

            assert isinstance(result, EnvLookupOutput)
            assert result.show_confirm is False  # from env var
            assert result.multi_goal_mode is False  # from env var

    def test_sanitize_json_response(self):
        """Test JSON response sanitization."""
        # Test with markdown code blocks
        response_with_markdown = '```json\n{"test": "value"}\n```'
        sanitized = self.tool_activities.sanitize_json_response(response_with_markdown)
        assert sanitized == '{"test": "value"}'

        # Test with extra whitespace
        response_with_whitespace = '  \n{"test": "value"}  \n'
        sanitized = self.tool_activities.sanitize_json_response(
            response_with_whitespace
        )
        assert sanitized == '{"test": "value"}'

    def test_parse_json_response_success(self):
        """Test successful JSON parsing."""
        json_string = '{"next": "confirm", "tool": "TestTool"}'
        result = self.tool_activities.parse_json_response(json_string)

        assert isinstance(result, dict)
        assert result["next"] == "confirm"
        assert result["tool"] == "TestTool"

    def test_parse_json_response_failure(self):
        """Test JSON parsing with invalid JSON."""
        invalid_json = "Not valid JSON"

        with pytest.raises(Exception):  # Should raise JSON parsing error
            self.tool_activities.parse_json_response(invalid_json)


class TestDynamicToolActivity:
    """Test cases for dynamic_tool_activity."""

    @pytest.mark.asyncio
    async def test_dynamic_tool_activity_sync_handler(self):
        """Test dynamic tool activity with synchronous handler."""
        # Mock the activity info and payload converter
        mock_info = MagicMock()
        mock_info.activity_type = "TestTool"

        mock_payload_converter = MagicMock()
        mock_payload = MagicMock()
        mock_payload.payload = b'{"test_arg": "test_value"}'
        mock_payload_converter.from_payload.return_value = {"test_arg": "test_value"}

        # Mock the handler function
        def mock_handler(args):
            return {"result": f"Handled {args['test_arg']}"}

        with patch("temporalio.activity.info", return_value=mock_info), patch(
            "temporalio.activity.payload_converter", return_value=mock_payload_converter
        ), patch("tools.get_handler", return_value=mock_handler):
            activity_env = ActivityEnvironment()
            result = await activity_env.run(dynamic_tool_activity, [mock_payload])

            assert isinstance(result, dict)
            assert result["result"] == "Handled test_value"

    @pytest.mark.asyncio
    async def test_dynamic_tool_activity_async_handler(self):
        """Test dynamic tool activity with asynchronous handler."""
        # Mock the activity info and payload converter
        mock_info = MagicMock()
        mock_info.activity_type = "AsyncTestTool"

        mock_payload_converter = MagicMock()
        mock_payload = MagicMock()
        mock_payload.payload = b'{"test_arg": "async_test"}'
        mock_payload_converter.from_payload.return_value = {"test_arg": "async_test"}

        # Mock the async handler function
        async def mock_async_handler(args):
            return {"async_result": f"Async handled {args['test_arg']}"}

        with patch("temporalio.activity.info", return_value=mock_info), patch(
            "temporalio.activity.payload_converter", return_value=mock_payload_converter
        ), patch("tools.get_handler", return_value=mock_async_handler):
            activity_env = ActivityEnvironment()
            result = await activity_env.run(dynamic_tool_activity, [mock_payload])

            assert isinstance(result, dict)
            assert result["async_result"] == "Async handled async_test"


class TestToolActivitiesIntegration:
    """Integration tests for ToolActivities in a real Temporal environment."""

    @pytest.mark.asyncio
    async def test_activities_in_worker(self, client: Client):
        """Test activities can be registered and executed in a worker."""
        # task_queue_name = str(uuid.uuid4())
        tool_activities = ToolActivities()

        # Test get_wf_env_vars activity using ActivityEnvironment
        env_input = EnvLookupInput(
            show_confirm_env_var_name="TEST_CONFIRM", show_confirm_default=False
        )

        activity_env = ActivityEnvironment()
        result = await activity_env.run(tool_activities.get_wf_env_vars, env_input)

        assert isinstance(result, EnvLookupOutput)
        assert isinstance(result.show_confirm, bool)
        assert isinstance(result.multi_goal_mode, bool)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.tool_activities = ToolActivities()

    @pytest.mark.asyncio
    async def test_agent_validatePrompt_with_empty_conversation_history(
        self, sample_agent_goal
    ):
        """Test validation with empty conversation history."""
        validation_input = ValidationInput(
            prompt="Test prompt",
            conversation_history={"messages": []},
            agent_goal=sample_agent_goal,
        )

        mock_response = {"validationResult": True, "validationFailedReason": {}}

        with patch.object(
            self.tool_activities, "agent_tool_planner", new_callable=AsyncMock
        ) as mock_planner:
            mock_planner.return_value = mock_response

            activity_env = ActivityEnvironment()
            result = await activity_env.run(
                self.tool_activities.agent_validatePrompt, validation_input
            )

            assert isinstance(result, ValidationResult)
            assert result.validationResult
            assert result.validationFailedReason == {}

    @pytest.mark.asyncio
    async def test_agent_tool_planner_with_long_prompt(self):
        """Test toolPlanner with very long prompt."""
        long_prompt = "This is a very long prompt " * 100
        tool_prompt_input = ToolPromptInput(
            prompt=long_prompt, context_instructions="Test context instructions"
        )

        # Mock the completion response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = '{"next": "done", "response": "Processed long prompt"}'

        with patch.object(
            self.tool_activities.llm_manager, "call_llm", new_callable=AsyncMock
        ) as mock_call_llm:
            mock_call_llm.return_value = mock_response
            activity_env = ActivityEnvironment()
            result = await activity_env.run(
                self.tool_activities.agent_tool_planner, tool_prompt_input
            )

            assert isinstance(result, dict)
            assert result["next"] == "done"
            assert "Processed long prompt" in result["response"]

    @pytest.mark.asyncio
    async def test_sanitize_json_with_various_formats(self):
        """Test JSON sanitization with various input formats."""
        # Test markdown code blocks
        markdown_json = '```json\n{"test": "value"}\n```'
        result = self.tool_activities.sanitize_json_response(markdown_json)
        assert result == '{"test": "value"}'

        # Test with extra whitespace
        whitespace_json = '   \n  {"test": "value"}  \n  '
        result = self.tool_activities.sanitize_json_response(whitespace_json)
        assert result == '{"test": "value"}'

        # Test already clean JSON
        clean_json = '{"test": "value"}'
        result = self.tool_activities.sanitize_json_response(clean_json)
        assert result == '{"test": "value"}'

    @pytest.mark.asyncio
    async def test_parse_json_response_with_invalid_json(self):
        """Test JSON parsing with invalid JSON."""
        with pytest.raises(json.JSONDecodeError):
            self.tool_activities.parse_json_response("Invalid JSON {test: value")

    @pytest.mark.asyncio
    async def test_get_wf_env_vars_with_various_env_values(self):
        """Test environment variable parsing with different values."""
        # Test with "true" string
        with patch.dict(os.environ, {"TEST_CONFIRM": "true"}):
            env_input = EnvLookupInput(
                show_confirm_env_var_name="TEST_CONFIRM", show_confirm_default=False
            )

            activity_env = ActivityEnvironment()
            result = await activity_env.run(
                self.tool_activities.get_wf_env_vars, env_input
            )

            assert result.show_confirm

        # Test with "false" string
        with patch.dict(os.environ, {"TEST_CONFIRM": "false"}):
            env_input = EnvLookupInput(
                show_confirm_env_var_name="TEST_CONFIRM", show_confirm_default=True
            )

            activity_env = ActivityEnvironment()
            result = await activity_env.run(
                self.tool_activities.get_wf_env_vars, env_input
            )

            assert not result.show_confirm

        # Test with missing env var (should use default)
        with patch.dict(os.environ, {}, clear=True):
            env_input = EnvLookupInput(
                show_confirm_env_var_name="MISSING_VAR", show_confirm_default=True
            )

            activity_env = ActivityEnvironment()
            result = await activity_env.run(
                self.tool_activities.get_wf_env_vars, env_input
            )

            assert result.show_confirm


class TestMCPIntegration:
    @pytest.mark.asyncio
    async def test_convert_args_types(self):
        from activities.tool_activities import _convert_args_types

        args = {
            "int_val": "123",
            "float_val": "123.45",
            "bool_true": "true",
            "bool_false": "False",
            "string": "text",
            "other": 5,
        }
        converted = _convert_args_types(args)
        assert converted["int_val"] == 123
        assert converted["float_val"] == 123.45
        assert converted["bool_true"] is True
        assert converted["bool_false"] is False
        assert converted["string"] == "text"
        assert converted["other"] == 5

    @pytest.mark.asyncio
    async def test_dynamic_tool_activity_mcp_call(self):
        mcp_def = MCPServerDefinition(
            name="stripe", command="python", args=["server.py"]
        )
        payload = MagicMock()
        payload.payload = b'{"server_definition": null, "amount": "10", "flag": "true"}'
        mock_info = MagicMock()
        mock_info.activity_type = "list_products"

        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def dummy_conn(*args, **kwargs):
            yield (None, None)

        class DummySession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                pass

            async def initialize(self):
                pass

            async def call_tool(self, tool_name, arguments=None):
                self.called_tool = tool_name
                self.called_args = arguments
                return MagicMock(content="ok")

        mock_payload_converter = MagicMock()
        mock_payload_converter.from_payload.return_value = {
            "server_definition": mcp_def,
            "amount": "10",
            "flag": "true",
        }

        with patch("activities.tool_activities._stdio_connection", dummy_conn), patch(
            "activities.tool_activities.ClientSession", return_value=DummySession()
        ), patch(
            "activities.tool_activities._build_connection",
            return_value={
                "type": "stdio",
                "command": "python",
                "args": ["server.py"],
                "env": {},
            },
        ), patch(
            "temporalio.activity.info", return_value=mock_info
        ), patch(
            "temporalio.activity.payload_converter", return_value=mock_payload_converter
        ):
            result = await ActivityEnvironment().run(dynamic_tool_activity, [payload])

        assert result["success"] is True
        assert result["tool"] == "list_products"

    @pytest.mark.asyncio
    async def test_mcp_tool_activity_failure(self):
        tool_activities = ToolActivities()
        mcp_def = MCPServerDefinition(
            name="stripe", command="python", args=["server.py"]
        )

        async def dummy_conn(*args, **kwargs):
            from contextlib import asynccontextmanager

            @asynccontextmanager
            async def cm():
                yield (None, None)

            return cm()

        class DummySession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                pass

            async def initialize(self):
                pass

            async def call_tool(self, tool_name, arguments=None):
                raise TypeError("boom")

        with patch("activities.tool_activities._stdio_connection", dummy_conn), patch(
            "activities.tool_activities.ClientSession", return_value=DummySession()
        ), patch(
            "activities.tool_activities._build_connection",
            return_value={
                "type": "stdio",
                "command": "python",
                "args": ["server.py"],
                "env": {},
            },
        ):
            result = await ActivityEnvironment().run(
                tool_activities.mcp_tool_activity,
                "list_products",
                {"server_definition": mcp_def, "amount": "10"},
            )

        assert result["success"] is False
        assert result["error_type"] == "TypeError"
