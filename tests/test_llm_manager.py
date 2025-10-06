"""Tests for LLM Manager with fallback support."""
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shared.llm_manager import LLMManager


class TestLLMManagerConfiguration:
    """Test cases for LLMManager configuration."""

    def setup_method(self):
        """Set up test environment for each test."""
        # Clear any existing environment variables
        env_vars_to_clear = [
            "LLM_MODEL",
            "LLM_KEY",
            "LLM_BASE_URL",
            "LLM_TIMEOUT_SECONDS",
            "LLM_FALLBACK_MODEL",
            "LLM_FALLBACK_KEY",
            "LLM_FALLBACK_BASE_URL",
            "LLM_FALLBACK_TIMEOUT_SECONDS",
            "LLM_RECOVERY_CHECK_INTERVAL_SECONDS",
        ]
        for var in env_vars_to_clear:
            os.environ.pop(var, None)

    def test_initialization_defaults(self):
        """Test default initialization values."""
        with patch.dict(os.environ, {}, clear=True):
            manager = LLMManager()

            assert manager.primary_model == "openai/gpt-4"
            assert manager.primary_key is None
            assert manager.primary_base_url is None
            assert manager.primary_timeout_seconds == 10
            assert manager.fallback_model is None
            assert manager.fallback_key is None
            assert manager.fallback_base_url is None
            assert manager.fallback_timeout_seconds == 10

    def test_initialization_with_environment_variables(self):
        """Test initialization with custom environment variables."""
        with patch.dict(
            os.environ,
            {
                "LLM_MODEL": "anthropic/claude-3-5-sonnet-20241022",
                "LLM_KEY": "primary-key-123",
                "LLM_BASE_URL": "https://primary.api.com",
                "LLM_TIMEOUT_SECONDS": "30",
                "LLM_FALLBACK_MODEL": "openai/gpt-4o",
                "LLM_FALLBACK_KEY": "fallback-key-456",
                "LLM_FALLBACK_BASE_URL": "https://fallback.api.com",
                "LLM_FALLBACK_TIMEOUT_SECONDS": "20",
            },
        ):
            manager = LLMManager()

            assert manager.primary_model == "anthropic/claude-3-5-sonnet-20241022"
            assert manager.primary_key == "primary-key-123"
            assert manager.primary_base_url == "https://primary.api.com"
            assert manager.primary_timeout_seconds == 30
            assert manager.fallback_model == "openai/gpt-4o"
            assert manager.fallback_key == "fallback-key-456"
            assert manager.fallback_base_url == "https://fallback.api.com"
            assert manager.fallback_timeout_seconds == 20


class TestLLMManagerPrimaryLLM:
    """Test cases for primary LLM functionality."""

    def setup_method(self):
        """Set up test environment for each test."""
        env_vars_to_clear = [
            "LLM_MODEL",
            "LLM_KEY",
            "LLM_BASE_URL",
            "LLM_TIMEOUT_SECONDS",
            "LLM_FALLBACK_MODEL",
            "LLM_FALLBACK_KEY",
            "LLM_FALLBACK_BASE_URL",
            "LLM_FALLBACK_TIMEOUT_SECONDS",
        ]
        for var in env_vars_to_clear:
            os.environ.pop(var, None)

    @pytest.mark.asyncio
    async def test_primary_llm_success(self):
        """Test successful primary LLM call."""
        with patch.dict(
            os.environ,
            {
                "LLM_MODEL": "openai/gpt-4",
                "LLM_KEY": "test-key-123",
            },
        ):
            manager = LLMManager()

            # Mock the completion function
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test response"

            with patch("shared.llm_manager.completion", return_value=mock_response):
                messages = [{"role": "user", "content": "Hello"}]
                response = await manager.call_llm(messages, fallback_mode=False)

                assert response == mock_response

    @pytest.mark.asyncio
    async def test_primary_llm_with_custom_base_url(self):
        """Test primary LLM call with custom base URL."""
        with patch.dict(
            os.environ,
            {
                "LLM_MODEL": "openai/gpt-4",
                "LLM_KEY": "test-key-123",
                "LLM_BASE_URL": "https://custom.api.com",
            },
        ):
            manager = LLMManager()

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"

            with patch("shared.llm_manager.completion", return_value=mock_response) as mock_completion:
                messages = [{"role": "user", "content": "Hello"}]
                await manager.call_llm(messages, fallback_mode=False)

                # Verify completion was called with base_url
                call_kwargs = mock_completion.call_args[1]
                assert call_kwargs["base_url"] == "https://custom.api.com"
                assert call_kwargs["model"] == "openai/gpt-4"
                assert call_kwargs["api_key"] == "test-key-123"

    @pytest.mark.asyncio
    async def test_primary_llm_custom_timeout(self):
        """Test primary LLM call with custom timeout."""
        with patch.dict(
            os.environ,
            {
                "LLM_MODEL": "openai/gpt-4",
                "LLM_KEY": "test-key-123",
                "LLM_TIMEOUT_SECONDS": "30",
            },
        ):
            manager = LLMManager()

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"

            with patch("shared.llm_manager.completion", return_value=mock_response) as mock_completion:
                messages = [{"role": "user", "content": "Hello"}]
                await manager.call_llm(messages, fallback_mode=False)

                # Verify timeout was passed correctly
                call_kwargs = mock_completion.call_args[1]
                assert call_kwargs["timeout"] == 30

    @pytest.mark.asyncio
    async def test_primary_llm_failure_raises_exception(self):
        """Test that primary LLM failure raises exception."""
        with patch.dict(
            os.environ,
            {
                "LLM_MODEL": "openai/gpt-4",
                "LLM_KEY": "test-key-123",
            },
        ):
            manager = LLMManager()

            # Mock completion to fail
            with patch("shared.llm_manager.completion", side_effect=Exception("API Error")):
                messages = [{"role": "user", "content": "Hello"}]

                with pytest.raises(Exception, match="API Error"):
                    await manager.call_llm(messages, fallback_mode=False)


class TestLLMManagerFallbackLLM:
    """Test cases for fallback LLM functionality."""

    def setup_method(self):
        """Set up test environment for each test."""
        env_vars_to_clear = [
            "LLM_MODEL",
            "LLM_KEY",
            "LLM_FALLBACK_MODEL",
            "LLM_FALLBACK_KEY",
            "LLM_FALLBACK_BASE_URL",
            "LLM_FALLBACK_TIMEOUT_SECONDS",
        ]
        for var in env_vars_to_clear:
            os.environ.pop(var, None)

    @pytest.mark.asyncio
    async def test_fallback_llm_success(self):
        """Test successful fallback LLM call when in fallback mode."""
        with patch.dict(
            os.environ,
            {
                "LLM_MODEL": "openai/gpt-4",
                "LLM_KEY": "test-key-123",
                "LLM_FALLBACK_MODEL": "anthropic/claude-3-5-sonnet-20241022",
                "LLM_FALLBACK_KEY": "fallback-key-456",
            },
        ):
            manager = LLMManager()

            # Mock the completion function
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Fallback response"

            with patch("shared.llm_manager.completion", return_value=mock_response):
                messages = [{"role": "user", "content": "Hello"}]
                response = await manager.call_llm(messages, fallback_mode=True)

                assert response == mock_response

    @pytest.mark.asyncio
    async def test_no_fallback_configured(self):
        """Test error when fallback is needed but not configured."""
        with patch.dict(
            os.environ,
            {
                "LLM_MODEL": "openai/gpt-4",
                "LLM_KEY": "test-key-123",
            },
        ):
            manager = LLMManager()

            messages = [{"role": "user", "content": "Hello"}]

            with pytest.raises(Exception, match="No fallback model configured"):
                await manager.call_llm(messages, fallback_mode=True)

    @pytest.mark.asyncio
    async def test_fallback_llm_with_custom_base_url(self):
        """Test fallback LLM call with custom base URL."""
        with patch.dict(
            os.environ,
            {
                "LLM_MODEL": "openai/gpt-4",
                "LLM_KEY": "test-key-123",
                "LLM_FALLBACK_MODEL": "anthropic/claude-3-5-sonnet-20241022",
                "LLM_FALLBACK_KEY": "fallback-key-456",
                "LLM_FALLBACK_BASE_URL": "https://custom.fallback.com",
            },
        ):
            manager = LLMManager()

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Fallback response"

            with patch("shared.llm_manager.completion", return_value=mock_response) as mock_completion:
                messages = [{"role": "user", "content": "Hello"}]
                await manager.call_llm(messages, fallback_mode=True)

                # Verify completion was called with fallback base_url
                call_kwargs = mock_completion.call_args[1]
                assert call_kwargs["base_url"] == "https://custom.fallback.com"
                assert call_kwargs["model"] == "anthropic/claude-3-5-sonnet-20241022"
                assert call_kwargs["api_key"] == "fallback-key-456"

    @pytest.mark.asyncio
    async def test_fallback_llm_custom_timeout(self):
        """Test fallback LLM call with custom timeout."""
        with patch.dict(
            os.environ,
            {
                "LLM_MODEL": "openai/gpt-4",
                "LLM_KEY": "test-key-123",
                "LLM_FALLBACK_MODEL": "anthropic/claude-3-5-sonnet-20241022",
                "LLM_FALLBACK_KEY": "fallback-key-456",
                "LLM_FALLBACK_TIMEOUT_SECONDS": "20",
            },
        ):
            manager = LLMManager()

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"

            with patch("shared.llm_manager.completion", return_value=mock_response) as mock_completion:
                messages = [{"role": "user", "content": "Hello"}]
                await manager.call_llm(messages, fallback_mode=True)

                # Verify timeout was passed correctly
                call_kwargs = mock_completion.call_args[1]
                assert call_kwargs["timeout"] == 20

    @pytest.mark.asyncio
    async def test_both_llms_fail(self):
        """Test error when both primary and fallback LLMs fail."""
        with patch.dict(
            os.environ,
            {
                "LLM_MODEL": "openai/gpt-4",
                "LLM_KEY": "test-key-123",
                "LLM_FALLBACK_MODEL": "anthropic/claude-3-5-sonnet-20241022",
                "LLM_FALLBACK_KEY": "fallback-key-456",
            },
        ):
            manager = LLMManager()

            # Mock completion to fail
            with patch("shared.llm_manager.completion", side_effect=Exception("Connection failed")):
                messages = [{"role": "user", "content": "Hello"}]

                with pytest.raises(Exception, match="Fallback LLM failed"):
                    await manager.call_llm(messages, fallback_mode=True)


class TestLLMManagerMessageHandling:
    """Test cases for message handling."""

    def setup_method(self):
        """Set up test environment for each test."""
        env_vars_to_clear = ["LLM_MODEL", "LLM_KEY"]
        for var in env_vars_to_clear:
            os.environ.pop(var, None)

    @pytest.mark.asyncio
    async def test_message_format_single_message(self):
        """Test that single message is passed correctly to the LLM."""
        with patch.dict(
            os.environ,
            {
                "LLM_MODEL": "openai/gpt-4",
                "LLM_KEY": "test-key-123",
            },
        ):
            manager = LLMManager()

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"

            with patch("shared.llm_manager.completion", return_value=mock_response) as mock_completion:
                messages = [{"role": "user", "content": "Hello"}]
                await manager.call_llm(messages, fallback_mode=False)

                # Verify messages were passed correctly
                call_kwargs = mock_completion.call_args[1]
                assert call_kwargs["messages"] == messages

    @pytest.mark.asyncio
    async def test_message_format_multiple_messages(self):
        """Test that multiple messages are passed correctly to the LLM."""
        with patch.dict(
            os.environ,
            {
                "LLM_MODEL": "openai/gpt-4",
                "LLM_KEY": "test-key-123",
            },
        ):
            manager = LLMManager()

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"

            with patch("shared.llm_manager.completion", return_value=mock_response) as mock_completion:
                messages = [
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                    {"role": "user", "content": "How are you?"},
                ]
                await manager.call_llm(messages, fallback_mode=False)

                # Verify messages were passed correctly
                call_kwargs = mock_completion.call_args[1]
                assert call_kwargs["messages"] == messages
                assert len(call_kwargs["messages"]) == 4