"""
Unit tests for LLMManager class.

Tests all methods except _save_debug_output and _cleanup_old_debug_files.
All function calls to other functions are mocked as requested.
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from shared.llm_manager import LLMManager


class TestLLMManager:
    """Test cases for LLMManager class."""

    def setup_method(self):
        """Reset singleton before each test."""
        LLMManager._reset_singleton()

    def teardown_method(self):
        """Clean up after each test."""
        LLMManager._reset_singleton()

    @patch.dict(
        os.environ,
        {
            "LLM_MODEL": "test/primary-model",
            "LLM_KEY": "primary-key",
            "LLM_BASE_URL": "https://primary.api.com",
            "LLM_TIMEOUT_SECONDS": "15",
            "LLM_FALLBACK_MODEL": "test/fallback-model",
            "LLM_FALLBACK_KEY": "fallback-key",
            "LLM_FALLBACK_BASE_URL": "https://fallback.api.com",
            "LLM_FALLBACK_TIMEOUT_SECONDS": "20",
            "LLM_RECOVERY_CHECK_INTERVAL_MINUTES": "3",
            "LLM_DEBUG_OUTPUT": "true",
            "LLM_DEBUG_OUTPUT_DIR": "/tmp/debug",
        },
    )
    @patch("shared.llm_manager.LLMManager._log_configuration")
    def test_init_with_all_config(self, mock_log_config):
        """Test initialization with all environment variables set."""
        manager = LLMManager()

        assert manager.primary_model == "test/primary-model"
        assert manager.primary_key == "primary-key"
        assert manager.primary_base_url == "https://primary.api.com"
        assert manager.primary_timeout_seconds == 15
        assert manager.fallback_model == "test/fallback-model"
        assert manager.fallback_key == "fallback-key"
        assert manager.fallback_base_url == "https://fallback.api.com"
        assert manager.fallback_timeout_seconds == 20
        assert manager.recovery_check_interval_minutes == 3
        assert manager.debug_output_enabled is True
        assert manager.debug_output_dir == "/tmp/debug"
        assert manager.using_fallback is False
        assert manager.primary_failure_time is None
        assert manager.last_recovery_check is None

        mock_log_config.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    @patch("shared.llm_manager.LLMManager._log_configuration")
    def test_init_with_minimal_config(self, mock_log_config):
        """Test initialization with minimal environment variables."""
        manager = LLMManager()

        assert manager.primary_model == "openai/gpt-4"  # default
        assert manager.primary_key is None
        assert manager.primary_base_url is None
        assert manager.primary_timeout_seconds == 10  # default
        assert manager.fallback_model is None
        assert manager.fallback_key is None
        assert manager.fallback_base_url is None
        assert manager.fallback_timeout_seconds == 10  # default
        assert manager.recovery_check_interval_minutes == 5  # default
        assert manager.debug_output_enabled is False  # default
        assert manager.debug_output_dir == "./debug_llm_calls"  # default

        mock_log_config.assert_called_once()

    @patch("shared.llm_manager.LLMManager._log_configuration")
    def test_singleton_pattern(self, mock_log_config):
        """Test that LLMManager implements singleton pattern correctly."""
        manager1 = LLMManager()
        manager2 = LLMManager()

        assert manager1 is manager2
        assert LLMManager._initialized is True
        # _log_configuration should only be called once
        mock_log_config.assert_called_once()

    def test_log_configuration_with_fallback(self, capsys):
        """Test _log_configuration with fallback configured."""
        with patch.dict(
            os.environ,
            {
                "LLM_MODEL": "test/primary",
                "LLM_KEY": "primary-key",
                "LLM_FALLBACK_MODEL": "test/fallback",
                "LLM_FALLBACK_KEY": "fallback-key",
                "LLM_DEBUG_OUTPUT": "true",
                "LLM_DEBUG_OUTPUT_DIR": "/custom/debug",
            },
        ):
            LLMManager()

        captured = capsys.readouterr()
        assert "Primary model: test/primary" in captured.out
        assert "Primary API key: ***set***" in captured.out
        assert "Fallback model: test/fallback" in captured.out
        assert "Fallback API key: ***set***" in captured.out
        assert "Debug output enabled: /custom/debug" in captured.out

    def test_log_configuration_without_fallback(self, capsys):
        """Test _log_configuration without fallback configured."""
        with patch.dict(
            os.environ,
            {"LLM_MODEL": "test/primary", "LLM_DEBUG_OUTPUT": "false"},
            clear=True,
        ):
            LLMManager()

        captured = capsys.readouterr()
        assert "Primary API key: not set" in captured.out
        assert "No fallback model configured" in captured.out
        assert "Debug output disabled" in captured.out

    @pytest.mark.asyncio
    @patch("shared.llm_manager.LLMManager._handle_debug")
    @patch("shared.llm_manager.LLMManager._recover_from_fallback")
    @patch("shared.llm_manager.LLMManager._call_primary_llm")
    async def test_call_llm_uses_primary_when_not_using_fallback(
        self, mock_call_primary, mock_recover, mock_handle_debug
    ):
        """Test call_llm uses primary LLM when not using fallback."""
        manager = LLMManager()
        manager.using_fallback = False

        messages = [{"role": "user", "content": "test"}]
        expected_response = {"choices": [{"message": {"content": "response"}}]}
        mock_call_primary.return_value = expected_response

        result = await manager.call_llm(messages)

        mock_handle_debug.assert_called_once_with(messages)
        mock_recover.assert_called_once()
        mock_call_primary.assert_called_once_with(messages)
        assert result == expected_response

    @pytest.mark.asyncio
    @patch("shared.llm_manager.LLMManager._handle_debug")
    @patch("shared.llm_manager.LLMManager._recover_from_fallback")
    @patch("shared.llm_manager.LLMManager._call_fallback_llm")
    async def test_call_llm_uses_fallback_when_using_fallback(
        self, mock_call_fallback, mock_recover, mock_handle_debug
    ):
        """Test call_llm uses fallback LLM when using fallback."""
        manager = LLMManager()
        manager.using_fallback = True

        messages = [{"role": "user", "content": "test"}]
        expected_response = {"choices": [{"message": {"content": "response"}}]}
        mock_call_fallback.return_value = expected_response

        result = await manager.call_llm(messages)

        mock_handle_debug.assert_called_once_with(messages)
        mock_recover.assert_called_once()
        mock_call_fallback.assert_called_once_with(messages)
        assert result == expected_response

    @pytest.mark.asyncio
    @patch("shared.llm_manager.completion")
    async def test_call_primary_llm_success(self, mock_completion):
        """Test successful primary LLM call."""
        manager = LLMManager()
        manager.primary_model = "test/model"
        manager.primary_key = "test-key"
        manager.primary_base_url = "https://test.api.com"
        manager.primary_timeout_seconds = 15

        messages = [{"role": "user", "content": "test"}]
        expected_response = {"choices": [{"message": {"content": "response"}}]}
        mock_completion.return_value = expected_response

        result = await manager._call_primary_llm(messages)

        mock_completion.assert_called_once_with(
            model="test/model",
            messages=messages,
            api_key="test-key",
            base_url="https://test.api.com",
            timeout=15,
        )
        assert result == expected_response

    @pytest.mark.asyncio
    @patch("shared.llm_manager.completion")
    async def test_call_primary_llm_success_without_base_url(self, mock_completion):
        """Test successful primary LLM call without base URL."""
        manager = LLMManager()
        manager.primary_model = "test/model"
        manager.primary_key = "test-key"
        manager.primary_base_url = None
        manager.primary_timeout_seconds = 12

        messages = [{"role": "user", "content": "test"}]
        expected_response = {"choices": [{"message": {"content": "response"}}]}
        mock_completion.return_value = expected_response

        result = await manager._call_primary_llm(messages)

        mock_completion.assert_called_once_with(
            model="test/model", messages=messages, api_key="test-key", timeout=12
        )
        assert result == expected_response

    @patch.dict(os.environ, {"LLM_TIMEOUT_SECONDS": "25"})
    @patch("shared.llm_manager.LLMManager._log_configuration")
    def test_init_with_custom_timeout(self, mock_log_config):
        """Test initialization with custom timeout configuration."""
        manager = LLMManager()

        assert manager.primary_timeout_seconds == 25

        mock_log_config.assert_called_once()

    @patch.dict(os.environ, {"LLM_FALLBACK_TIMEOUT_SECONDS": "30"})
    @patch("shared.llm_manager.LLMManager._log_configuration")
    def test_init_with_custom_fallback_timeout(self, mock_log_config):
        """Test initialization with custom fallback timeout configuration."""
        manager = LLMManager()

        assert manager.fallback_timeout_seconds == 30

        mock_log_config.assert_called_once()

    @pytest.mark.asyncio
    @patch("shared.llm_manager.completion")
    @patch("shared.llm_manager.LLMManager._primary_llm_call_failed")
    async def test_call_primary_llm_failure(self, mock_failed_handler, mock_completion):
        """Test primary LLM call failure handling."""
        manager = LLMManager()

        messages = [{"role": "user", "content": "test"}]
        exception = Exception("API Error")
        mock_completion.side_effect = exception
        expected_response = {"fallback": "response"}
        mock_failed_handler.return_value = expected_response

        result = await manager._call_primary_llm(messages)

        mock_failed_handler.assert_called_once_with(messages, exception)
        assert result == expected_response

    @pytest.mark.asyncio
    @patch("shared.llm_manager.LLMManager._should_use_fallback")
    @patch("shared.llm_manager.LLMManager._initial_fallback_llm_call")
    async def test_primary_llm_call_failed_with_fallback(
        self, mock_initial_fallback, mock_should_use_fallback
    ):
        """Test primary LLM call failed with fallback available."""
        manager = LLMManager()

        messages = [{"role": "user", "content": "test"}]
        exception = Exception("Primary failed")
        mock_should_use_fallback.return_value = True
        expected_response = {"fallback": "response"}
        mock_initial_fallback.return_value = expected_response

        result = await manager._primary_llm_call_failed(messages, exception)

        mock_should_use_fallback.assert_called_once()
        mock_initial_fallback.assert_called_once_with(messages)
        assert result == expected_response

    @pytest.mark.asyncio
    @patch("shared.llm_manager.LLMManager._should_use_fallback")
    async def test_primary_llm_call_failed_without_fallback(
        self, mock_should_use_fallback
    ):
        """Test primary LLM call failed without fallback available."""
        manager = LLMManager()

        messages = [{"role": "user", "content": "test"}]
        exception = Exception("Primary failed")
        mock_should_use_fallback.return_value = False

        with pytest.raises(Exception, match="Primary failed"):
            await manager._primary_llm_call_failed(messages, exception)

        mock_should_use_fallback.assert_called_once()

    @pytest.mark.asyncio
    @patch("shared.llm_manager.LLMManager._call_fallback_llm")
    @patch("shared.llm_manager.datetime")
    async def test_initial_fallback_llm_call(self, mock_datetime, mock_call_fallback):
        """Test initial fallback LLM call sets state correctly."""
        manager = LLMManager()
        manager.using_fallback = False
        manager.primary_failure_time = None

        now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = now

        messages = [{"role": "user", "content": "test"}]
        expected_response = {"fallback": "response"}
        mock_call_fallback.return_value = expected_response

        result = await manager._initial_fallback_llm_call(messages)

        assert manager.using_fallback is True
        assert manager.primary_failure_time == now
        mock_call_fallback.assert_called_once_with(messages)
        assert result == expected_response

    @pytest.mark.asyncio
    @patch("shared.llm_manager.completion")
    async def test_call_fallback_llm_success(self, mock_completion):
        """Test successful fallback LLM call."""
        manager = LLMManager()
        manager.fallback_model = "test/fallback"
        manager.fallback_key = "fallback-key"
        manager.fallback_base_url = "https://fallback.api.com"
        manager.fallback_timeout_seconds = 18

        messages = [{"role": "user", "content": "test"}]
        expected_response = {"choices": [{"message": {"content": "response"}}]}
        mock_completion.return_value = expected_response

        result = await manager._call_fallback_llm(messages)

        mock_completion.assert_called_once_with(
            model="test/fallback",
            messages=messages,
            api_key="fallback-key",
            base_url="https://fallback.api.com",
            timeout=18,
        )
        assert result == expected_response

    @pytest.mark.asyncio
    @patch("shared.llm_manager.completion")
    async def test_call_fallback_llm_success_without_base_url(self, mock_completion):
        """Test successful fallback LLM call without base URL."""
        manager = LLMManager()
        manager.fallback_model = "test/fallback"
        manager.fallback_key = "fallback-key"
        manager.fallback_base_url = None
        manager.fallback_timeout_seconds = 14

        messages = [{"role": "user", "content": "test"}]
        expected_response = {"choices": [{"message": {"content": "response"}}]}
        mock_completion.return_value = expected_response

        result = await manager._call_fallback_llm(messages)

        mock_completion.assert_called_once_with(
            model="test/fallback", messages=messages, api_key="fallback-key", timeout=14
        )
        assert result == expected_response

    @pytest.mark.asyncio
    @patch("shared.llm_manager.completion")
    async def test_call_fallback_llm_failure(self, mock_completion):
        """Test fallback LLM call failure."""
        manager = LLMManager()
        manager.primary_model = "test/primary"
        manager.fallback_model = "test/fallback"

        messages = [{"role": "user", "content": "test"}]
        mock_completion.side_effect = Exception("Fallback failed")

        with pytest.raises(Exception, match="Both primary and fallback LLMs failed"):
            await manager._call_fallback_llm(messages)

    @pytest.mark.asyncio
    @patch("shared.llm_manager.LLMManager._primary_llm_failure_retry")
    @patch("shared.llm_manager.LLMManager._try_primary")
    async def test_recover_from_fallback_successful_recovery(
        self, mock_try_primary, mock_failure_retry
    ):
        """Test successful recovery from fallback to primary."""
        manager = LLMManager()
        manager.using_fallback = True
        manager.primary_failure_time = datetime.now()

        mock_failure_retry.return_value = True
        mock_try_primary.return_value = True

        await manager._recover_from_fallback()

        assert manager.using_fallback is False
        assert manager.primary_failure_time is None
        mock_failure_retry.assert_called_once()
        mock_try_primary.assert_called_once()

    @pytest.mark.asyncio
    @patch("shared.llm_manager.LLMManager._primary_llm_failure_retry")
    @patch("shared.llm_manager.LLMManager._try_primary")
    async def test_recover_from_fallback_failed_recovery(
        self, mock_try_primary, mock_failure_retry
    ):
        """Test failed recovery attempt from fallback."""
        manager = LLMManager()
        manager.using_fallback = True
        failure_time = datetime.now()
        manager.primary_failure_time = failure_time

        mock_failure_retry.return_value = True
        mock_try_primary.return_value = False

        await manager._recover_from_fallback()

        # State should remain unchanged
        assert manager.using_fallback is True
        assert manager.primary_failure_time == failure_time
        mock_failure_retry.assert_called_once()
        mock_try_primary.assert_called_once()

    @pytest.mark.asyncio
    @patch("shared.llm_manager.LLMManager._primary_llm_failure_retry")
    async def test_recover_from_fallback_not_time_yet(self, mock_failure_retry):
        """Test recovery not attempted when interval hasn't passed."""
        manager = LLMManager()
        manager.using_fallback = True
        failure_time = datetime.now()
        manager.primary_failure_time = failure_time

        mock_failure_retry.return_value = False

        await manager._recover_from_fallback()

        # State should remain unchanged
        assert manager.using_fallback is True
        assert manager.primary_failure_time == failure_time
        mock_failure_retry.assert_called_once()

    @pytest.mark.asyncio
    async def test_recover_from_fallback_not_using_fallback(self):
        """Test recovery is skipped when not using fallback."""
        manager = LLMManager()
        manager.using_fallback = False

        # Should return early without doing anything
        await manager._recover_from_fallback()

        assert manager.using_fallback is False

    @pytest.mark.asyncio
    @patch("shared.llm_manager.LLMManager._save_debug_output")
    async def test_handle_debug_with_debug_enabled(self, mock_save_debug):
        """Test _handle_debug with debug output enabled."""
        manager = LLMManager()
        manager.debug_output_enabled = True

        messages = [{"role": "user", "content": "test"}]

        await manager._handle_debug(messages)

        mock_save_debug.assert_called_once_with(messages)

    @pytest.mark.asyncio
    @patch("shared.llm_manager.LLMManager._save_debug_output")
    async def test_handle_debug_with_debug_disabled(self, mock_save_debug):
        """Test _handle_debug with debug output disabled."""
        manager = LLMManager()
        manager.debug_output_enabled = False

        messages = [{"role": "user", "content": "test"}]

        await manager._handle_debug(messages)

        mock_save_debug.assert_not_called()

    def test_should_use_fallback_with_fallback_configured(self):
        """Test _should_use_fallback when fallback is configured."""
        manager = LLMManager()
        manager.fallback_model = "test/fallback"

        result = manager._should_use_fallback()

        assert result is True

    def test_should_use_fallback_without_fallback_configured(self):
        """Test _should_use_fallback when fallback is not configured."""
        manager = LLMManager()
        manager.fallback_model = None

        result = manager._should_use_fallback()

        assert result is False

    def test_should_use_fallback_with_empty_fallback_model(self):
        """Test _should_use_fallback when fallback model is empty string."""
        manager = LLMManager()
        manager.fallback_model = ""

        result = manager._should_use_fallback()

        assert result is False

    @patch("shared.llm_manager.datetime")
    def test_primary_llm_failure_retry_within_duration(self, mock_datetime):
        """Test _primary_llm_failure_retry within fallback duration."""
        manager = LLMManager()
        manager.recovery_check_interval_minutes = 10

        failure_time = datetime(2023, 1, 1, 12, 0, 0)
        current_time = datetime(2023, 1, 1, 12, 5, 0)  # 5 minutes later

        manager.primary_failure_time = failure_time
        mock_datetime.now.return_value = current_time

        result = manager._primary_llm_failure_retry()

        assert result is False

    @patch("shared.llm_manager.datetime")
    def test_primary_llm_failure_retry_beyond_duration(self, mock_datetime):
        """Test _primary_llm_failure_retry beyond fallback duration."""
        manager = LLMManager()
        manager.recovery_check_interval_minutes = 10

        failure_time = datetime(2023, 1, 1, 12, 0, 0)
        current_time = datetime(2023, 1, 1, 12, 15, 0)  # 15 minutes later

        manager.primary_failure_time = failure_time
        mock_datetime.now.return_value = current_time

        result = manager._primary_llm_failure_retry()

        assert result is True

    @patch("shared.llm_manager.datetime")
    def test_primary_llm_failure_retry_exactly_at_duration(self, mock_datetime):
        """Test _primary_llm_failure_retry exactly at fallback duration."""
        manager = LLMManager()
        manager.recovery_check_interval_minutes = 10

        failure_time = datetime(2023, 1, 1, 12, 0, 0)
        current_time = datetime(2023, 1, 1, 12, 10, 0)  # exactly 10 minutes later

        manager.primary_failure_time = failure_time
        mock_datetime.now.return_value = current_time

        result = manager._primary_llm_failure_retry()

        assert result is False  # Should be False since it's not > the duration

    @pytest.mark.asyncio
    @patch("shared.llm_manager.completion")
    @patch("shared.llm_manager.datetime")
    async def test_try_primary_success(self, mock_datetime, mock_completion):
        """Test successful primary LLM health check."""
        manager = LLMManager()
        manager.primary_model = "test/primary"
        manager.primary_key = "test-key"
        manager.primary_base_url = "https://test.api.com"

        now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = now
        mock_completion.return_value = {"status": "ok"}

        result = await manager._try_primary()

        assert result is True
        assert manager.last_recovery_check == now
        mock_completion.assert_called_once_with(
            model="test/primary",
            messages=[{"role": "user", "content": "Reply with 'OK' if you're working"}],
            api_key="test-key",
            max_tokens=10,
            timeout=5,
            base_url="https://test.api.com",
        )

    @pytest.mark.asyncio
    @patch("shared.llm_manager.completion")
    @patch("shared.llm_manager.datetime")
    async def test_try_primary_success_without_base_url(
        self, mock_datetime, mock_completion
    ):
        """Test successful primary LLM health check without base URL."""
        manager = LLMManager()
        manager.primary_model = "test/primary"
        manager.primary_key = "test-key"
        manager.primary_base_url = None

        now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = now
        mock_completion.return_value = {"status": "ok"}

        result = await manager._try_primary()

        assert result is True
        assert manager.last_recovery_check == now
        mock_completion.assert_called_once_with(
            model="test/primary",
            messages=[{"role": "user", "content": "Reply with 'OK' if you're working"}],
            api_key="test-key",
            max_tokens=10,
            timeout=5,
        )

    @pytest.mark.asyncio
    @patch("shared.llm_manager.completion")
    @patch("shared.llm_manager.datetime")
    async def test_try_primary_failure(self, mock_datetime, mock_completion):
        """Test failed primary LLM health check."""
        manager = LLMManager()

        now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = now
        mock_completion.side_effect = Exception("Health check failed")

        result = await manager._try_primary()

        assert result is False
        assert manager.last_recovery_check == now

    @patch("shared.llm_manager.LLMManager.get_current_model")
    def test_get_status_with_fallback_active(self, mock_get_current_model):
        """Test get_status when using fallback."""
        manager = LLMManager()
        manager.using_fallback = True
        manager.fallback_model = "test/fallback"
        failure_time = datetime(2023, 1, 1, 12, 0, 0)
        recovery_time = datetime(2023, 1, 1, 12, 5, 0)
        manager.primary_failure_time = failure_time
        manager.last_recovery_check = recovery_time

        mock_get_current_model.return_value = "test/fallback"

        with patch("shared.llm_manager.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 10, 0)
            status = manager.get_status()

        assert status["current_model"] == "test/fallback"
        assert status["using_fallback"] is True
        assert status["primary_failure_time"] == failure_time.isoformat()
        assert status["failure_duration_seconds"] == 600  # 10 minutes
        assert status["fallback_configured"] is True
        assert status["last_recovery_check"] == recovery_time.isoformat()

    @patch("shared.llm_manager.LLMManager.get_current_model")
    def test_get_status_with_primary_active(self, mock_get_current_model):
        """Test get_status when using primary."""
        manager = LLMManager()
        manager.using_fallback = False
        manager.primary_model = "test/primary"
        manager.fallback_model = None
        manager.primary_failure_time = None
        manager.last_recovery_check = None

        mock_get_current_model.return_value = "test/primary"

        status = manager.get_status()

        assert status["current_model"] == "test/primary"
        assert status["using_fallback"] is False
        assert status["primary_failure_time"] is None
        assert status["failure_duration_seconds"] is None
        assert status["fallback_configured"] is False
        assert status["last_recovery_check"] is None

    def test_get_current_model_primary(self):
        """Test get_current_model when using primary."""
        manager = LLMManager()
        manager.primary_model = "test/primary"
        manager.fallback_model = "test/fallback"
        manager.using_fallback = False

        result = manager.get_current_model()

        assert result == "test/primary"

    def test_get_current_model_fallback(self):
        """Test get_current_model when using fallback."""
        manager = LLMManager()
        manager.primary_model = "test/primary"
        manager.fallback_model = "test/fallback"
        manager.using_fallback = True

        result = manager.get_current_model()

        assert result == "test/fallback"

    def test_reset_singleton(self):
        """Test _reset_singleton resets the singleton state."""
        manager1 = LLMManager()
        assert LLMManager._instance is not None
        assert LLMManager._initialized is True

        LLMManager._reset_singleton()

        assert LLMManager._instance is None
        assert LLMManager._initialized is False

        manager2 = LLMManager()
        assert manager1 is not manager2
