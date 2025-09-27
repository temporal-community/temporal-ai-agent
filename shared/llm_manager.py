"""
LLM Manager with automatic fallback support.

Environment Variables:
    LLM_MODEL: Primary LLM model (e.g., "openai/gpt-4")
    LLM_KEY: API key for primary LLM
    LLM_BASE_URL: Optional custom base URL for primary LLM
    LLM_TIMEOUT_SECONDS: Timeout for primary LLM calls in seconds (default: 10)
    LLM_FALLBACK_MODEL: Fallback LLM model
    LLM_FALLBACK_KEY: API key for fallback LLM
    LLM_FALLBACK_BASE_URL: Optional custom base URL for fallback LLM
    LLM_FALLBACK_TIMEOUT_SECONDS: Timeout for fallback LLM calls in seconds (default: 10)
    LLM_RECOVERY_CHECK_INTERVAL_MINUTES: How often to check if primary recovered (default: 5)
    LLM_DEBUG_OUTPUT: Enable debug file output ("true"/"false", default: "false")
    LLM_DEBUG_OUTPUT_DIR: Directory for debug files (default: "./debug_llm_calls")

Usage:
    manager = LLMManager()
    response = await manager.call_llm([{"role": "user", "content": "Hello"}])
    status = manager.get_status()
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from litellm import completion
from temporalio import activity

load_dotenv(override=True)


class LLMManager:
    """
    Manages LLM calls with automatic fallback to secondary models.

    This class implements a singleton pattern to ensure consistent state across
    the application. It provides robust LLM calling with immediate fallback
    on failures and automatic recovery detection.

    Key Features:
    - Singleton pattern ensures one instance per process
    - Immediate fallback switching on any primary LLM failure
    - Periodic health checks to detect primary LLM recovery
    - Configurable fallback duration and recovery intervals
    - Optional debug file output for troubleshooting
    - Comprehensive logging for monitoring and debugging

    State Management:
    - using_fallback: Boolean indicating if currently using fallback LLM
    - primary_failure_time: Timestamp of when primary LLM first failed
    - last_recovery_check: Timestamp of last recovery attempt
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            print(f"[LLMManager.__new__] Creating new singleton instance")
            cls._instance = super(LLMManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize LLM Manager with primary and fallback configurations."""
        # Only initialize once due to singleton pattern
        if LLMManager._initialized:
            print(f"[LLMManager.__init__] Singleton already initialized, skipping")
            return

        print(f"[LLMManager.__init__] Initializing singleton instance")
        LLMManager._initialized = True
        # Primary LLM configuration
        self.primary_model = os.environ.get("LLM_MODEL", "openai/gpt-4")
        self.primary_key = os.environ.get("LLM_KEY")
        self.primary_base_url = os.environ.get("LLM_BASE_URL")
        self.primary_timeout_seconds = int(os.environ.get("LLM_TIMEOUT_SECONDS", "10"))

        # Fallback LLM configuration
        self.fallback_model = os.environ.get("LLM_FALLBACK_MODEL")
        self.fallback_key = os.environ.get("LLM_FALLBACK_KEY")
        self.fallback_base_url = os.environ.get("LLM_FALLBACK_BASE_URL")
        self.fallback_timeout_seconds = int(
            os.environ.get("LLM_FALLBACK_TIMEOUT_SECONDS", "10")
        )

        # Failure tracking
        self.primary_failure_time: Optional[datetime] = None
        self.using_fallback = False

        # Recovery check settings
        self.last_recovery_check: Optional[datetime] = None
        self.recovery_check_interval_minutes = int(
            os.environ.get("LLM_RECOVERY_CHECK_INTERVAL_MINUTES", "5")
        )

        # Debug file settings
        self.debug_output_enabled = (
            os.environ.get("LLM_DEBUG_OUTPUT", "false").lower() == "true"
        )
        self.debug_output_dir = os.environ.get(
            "LLM_DEBUG_OUTPUT_DIR", "./debug_llm_calls"
        )
        self._log_configuration()

    def _log_configuration(self):
        """Log the LLM configuration for debugging."""
        print(f"[LLMManager._log_configuration] LLM Manager initialized:")
        print(f"  Primary model: {self.primary_model}")
        print(f"  Primary API key: {'***set***' if self.primary_key else 'not set'}")
        print(f"  Primary base URL: {self.primary_base_url or 'default'}")

        if self.fallback_model:
            print(f"  Fallback model: {self.fallback_model}")
            print(
                f"  Fallback API key: {'***set***' if self.fallback_key else 'not set'}"
            )
            print(f"  Fallback base URL: {self.fallback_base_url or 'default'}")
            print(
                f"  Recovery check interval: {self.recovery_check_interval_minutes} minutes"
            )
        else:
            print(f"  No fallback model configured")

        if self.debug_output_enabled:
            print(f"  Debug output enabled: {self.debug_output_dir}")
        else:
            print(f"  Debug output disabled")

        print(f"  Initial state: using_fallback=False, primary_failure_time=None")

    async def call_llm(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Call LLM with automatic fallback support.

        Args:
            messages: The messages to send to the LLM

        Returns:
            The LLM response

        Raises:
            Exception: If both primary and fallback LLMs fail
        """
        await self._handle_debug(messages)

        # Check if we should try to recover from fallback mode. If we are using the fallback llm, this
        # checks if the conditions are such that the primary should be used again. If so, state variables
        # are reset to indicate the primary is usable again.
        await self._recover_from_fallback()

        # Determine which LLM to use
        if self.using_fallback:
            response = await self._call_fallback_llm(messages)
        else:
            # Try primary LLM
            response = await self._call_primary_llm(messages)

        return response

    async def _call_primary_llm(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """
        Call the primary LLM

        :param messages: LLM message
        :return: LLM response
        """
        activity.logger.debug(
            f"[LLMManager.call_llm] Attempting primary LLM call: {self.primary_model}"
        )
        try:
            completion_kwargs = {
                "model": self.primary_model,
                "messages": messages,
                "api_key": self.primary_key,
            }

            if self.primary_base_url:
                completion_kwargs["base_url"] = self.primary_base_url

            activity.logger.debug(
                f"[LLMManager._call_primary_llm] Calling litellm completion"
            )
            response = completion(
                **completion_kwargs, timeout=self.primary_timeout_seconds
            )
            activity.logger.debug(
                f"[LLMManager._call_primary_llm] Primary LLM call successful"
            )
        except Exception as primary_error:
            response = await self._primary_llm_call_failed(messages, primary_error)

        return response

    async def _primary_llm_call_failed(
        self, messages: list[dict[str, str]], primary_exception: Exception
    ) -> dict[str, Any]:
        """
        The primary LLM call failed. Perform fallback process.

        :param messages: Message to send to fallback LLM
        :param primary_exception: Primary LLM Exception
        :return:
        """
        activity.logger.warning(f"Primary LLM failed: {str(primary_exception)}")

        # Switch to fallback immediately on any failure (if available)
        if self._should_use_fallback():
            response = await self._initial_fallback_llm_call(messages)
        else:
            activity.logger.debug(
                f"[LLMManager.call_llm] No fallback configured, re-raising primary exception"
            )
            raise primary_exception
        return response

    async def _initial_fallback_llm_call(
        self, messages: list[dict[str, str]]
    ) -> dict[str, Any]:
        activity.logger.debug(
            f"[LLMManager.call_llm] Fallback available, switching to fallback mode"
        )
        self.primary_failure_time = datetime.now()
        self.using_fallback = True
        activity.logger.info(f"Switching to fallback LLM due to primary failure")
        response = await self._call_fallback_llm(messages)
        return response

    async def _call_fallback_llm(
        self, messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Call the fallback LLM."""
        activity.logger.debug(
            f"[LLMManager._call_fallback_llm] Starting fallback LLM call"
        )

        completion_kwargs = {
            "model": self.fallback_model,
            "messages": messages,
            "api_key": self.fallback_key,
        }

        if self.fallback_base_url:
            completion_kwargs["base_url"] = self.fallback_base_url

        try:
            response = completion(
                **completion_kwargs, timeout=self.fallback_timeout_seconds
            )
            activity.logger.info(
                f"Successfully used fallback LLM: {self.fallback_model}"
            )
            return response
        except Exception as fallback_error:
            activity.logger.error(f"Fallback LLM also failed: {str(fallback_error)}")
            raise Exception(
                f"Both primary and fallback LLMs failed. "
                f"Primary: {self.primary_model}, Fallback: {self.fallback_model}"
            )

    async def _recover_from_fallback(self):
        """
        If using the fallback LLM, determine if the conditions are such that a recovery to the primary is
        appropriate. If so, reset the LLMManager state accordingly.
        """
        if self.using_fallback and self._primary_llm_failure_retry():
            activity.logger.debug(
                f"[LLMManager.call_llm] Recovery check interval passed, attempting primary health check"
            )
            if await self._try_primary():
                self.using_fallback = False
                self.primary_failure_time = None
                activity.logger.info("Successfully recovered to primary LLM")
            else:
                activity.logger.debug(
                    f"[LLMManager.call_llm] Primary health check failed, staying in fallback mode"
                )

    async def _handle_debug(self, messages: list[dict[str, str]]):
        activity.logger.debug(
            f"[LLMManager.call_llm] Starting LLM call with {len(messages)} messages"
        )
        activity.logger.debug(
            f"[LLMManager.call_llm] Current state: using_fallback={self.using_fallback}, primary_failure_time={self.primary_failure_time}"
        )

        # Save debug output if enabled
        if self.debug_output_enabled:
            await self._save_debug_output(messages)

    def _should_use_fallback(self) -> bool:
        """
        Check if we should switch to the fallback LLM.
        """
        result = bool(self.fallback_model)
        return result

    def _primary_llm_failure_retry(self) -> bool:
        """
        Check if the fallback period has expired and we should retry the primary.
        """

        failure_duration = datetime.now() - self.primary_failure_time
        duration_minutes = failure_duration.total_seconds() / 60
        expired = failure_duration > timedelta(
            minutes=self.recovery_check_interval_minutes
        )
        activity.logger.debug(
            f"[LLMManager._fallback_period_expired] Duration since failure: {duration_minutes:.1f} minutes, threshold: {self.recovery_check_interval_minutes} minutes, expired: {expired}"
        )
        return expired

    async def _try_primary(self) -> bool:
        """
        Try to use the primary LLM with a simple test message.

        Returns:
            True if the primary LLM is working, False otherwise
        """
        activity.logger.debug(
            f"[LLMManager._try_primary] Starting primary LLM health check"
        )
        self.last_recovery_check = datetime.now()

        try:
            test_messages = [
                {"role": "user", "content": "Reply with 'OK' if you're working"}
            ]
            activity.logger.debug(
                f"[LLMManager._try_primary] Using test message for health check"
            )

            completion_kwargs = {
                "model": self.primary_model,
                "messages": test_messages,
                "api_key": self.primary_key,
                "max_tokens": 10,
                "timeout": 5,  # Short timeout for health check
            }

            if self.primary_base_url:
                completion_kwargs["base_url"] = self.primary_base_url

            activity.logger.debug(
                f"[LLMManager._try_primary] Calling litellm completion for health check"
            )
            # If an exception is not thrown, assume we are good to go.
            completion(**completion_kwargs)
            activity.logger.info("Primary LLM health check succeeded")
            return True

        except Exception as e:
            activity.logger.debug(f"Primary LLM health check failed: {str(e)}")
            return False

    def get_current_model(self) -> str:
        """
        Get the currently active model name.

        Returns:
            str: The name of the currently active LLM model (primary or fallback)
        """
        current = self.fallback_model if self.using_fallback else self.primary_model
        activity.logger.debug(
            f"[LLMManager.get_current_model] Current active model: {current} (using_fallback={self.using_fallback})"
        )
        return current

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the LLM manager.

        Returns:
            Dict[str, Any]: Status dictionary containing:
                - current_model: Currently active model name
                - using_fallback: Whether currently using fallback LLM
                - primary_failure_time: ISO timestamp of primary failure (if any)
                - failure_duration_seconds: Seconds since primary failure (if any)
                - fallback_configured: Whether fallback LLM is configured
                - last_recovery_check: ISO timestamp of last recovery check (if any)
        """
        status = {
            "current_model": self.get_current_model(),
            "using_fallback": self.using_fallback,
            "primary_failure_time": self.primary_failure_time.isoformat()
            if self.primary_failure_time
            else None,
            "failure_duration_seconds": (
                (datetime.now() - self.primary_failure_time).total_seconds()
                if self.primary_failure_time
                else None
            ),
            "fallback_configured": bool(self.fallback_model),
            "last_recovery_check": self.last_recovery_check.isoformat()
            if self.last_recovery_check
            else None,
        }
        activity.logger.debug(f"[LLMManager.get_status] Status: {status}")
        return status

    @classmethod
    def _reset_singleton(cls):
        """Reset the singleton instance. Only for testing purposes."""
        print(f"[LLMManager._reset_singleton] Resetting singleton instance")
        cls._instance = None
        cls._initialized = False

    async def _save_debug_output(self, messages: List[Dict[str, str]]) -> None:
        """Save LLM messages in a format that can be cut/pasted into an LLM interface."""
        activity.logger.debug(
            f"[LLMManager._save_debug_output] Starting debug output save"
        )
        try:
            # Create debug directory if it doesn't exist
            os.makedirs(self.debug_output_dir, exist_ok=True)

            # Clean up old files, keeping only the 20 most recent
            self._cleanup_old_debug_files()

            # Generate timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[
                :-3
            ]  # Include milliseconds
            filename = f"llm_call_{timestamp}.txt"
            filepath = os.path.join(self.debug_output_dir, filename)
            activity.logger.debug(
                f"[LLMManager._save_debug_output] Writing debug output to: {filepath}"
            )

            # Write to file
            with open(filepath, "w") as f:
                # Write header information
                f.write(f"=== LLM Debug Output ===\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Model: {self.get_current_model()}\n")
                f.write(f"Using Fallback: {self.using_fallback}\n")
                f.write("=" * 50 + "\n\n")

                # Write each message in a readable format
                activity.logger.debug(
                    f"[LLMManager._save_debug_output] Writing {len(messages)} messages to debug file"
                )
                for i, message in enumerate(messages, 1):
                    role = message.get("role", "unknown")
                    content = message.get("content", "")

                    f.write(f"As ({role.upper()}) :\n")
                    f.write(f"{content}\n")
                    f.write("\n" + "-" * 30 + "\n\n")

                # Add a section for easy copying
                f.write("=== FOR MANUAL TESTING ===\n")
                f.write("Copy the messages above and paste into your LLM interface.\n")

            activity.logger.debug(f"Saved LLM debug output to {filepath}")
        except Exception as e:
            activity.logger.warning(f"Failed to save LLM debug output: {str(e)}")

    def _cleanup_old_debug_files(self) -> None:
        """Keep only the 20 most recent debug files, delete older ones."""
        activity.logger.debug(
            f"[LLMManager._cleanup_old_debug_files] Starting cleanup of old debug files"
        )
        try:
            # Get all debug files in the directory
            debug_files = []
            activity.logger.debug(
                f"[LLMManager._cleanup_old_debug_files] Scanning directory: {self.debug_output_dir}"
            )
            for filename in os.listdir(self.debug_output_dir):
                if filename.startswith("llm_call_") and filename.endswith(".txt"):
                    filepath = os.path.join(self.debug_output_dir, filename)
                    if os.path.isfile(filepath):
                        # Get file modification time
                        mtime = os.path.getmtime(filepath)
                        debug_files.append((filepath, mtime))

            activity.logger.debug(
                f"[LLMManager._cleanup_old_debug_files] Found {len(debug_files)} debug files"
            )

            # Sort by modification time (newest first)
            debug_files.sort(key=lambda x: x[1], reverse=True)

            # Keep only the 20 most recent files, delete the rest
            if len(debug_files) > 20:
                files_to_delete = debug_files[20:]
                activity.logger.debug(
                    f"[LLMManager._cleanup_old_debug_files] Need to delete {len(files_to_delete)} old files"
                )
                for filepath, _ in files_to_delete:
                    try:
                        os.remove(filepath)
                        activity.logger.debug(
                            f"[LLMManager._cleanup_old_debug_files] Deleted old debug file: {filepath}"
                        )
                        activity.logger.debug(f"Deleted old debug file: {filepath}")
                    except OSError as e:
                        activity.logger.debug(
                            f"[LLMManager._cleanup_old_debug_files] Failed to delete {filepath}: {str(e)}"
                        )
                        activity.logger.warning(
                            f"Failed to delete old debug file {filepath}: {str(e)}"
                        )
            else:
                activity.logger.debug(
                    f"[LLMManager._cleanup_old_debug_files] No cleanup needed, {len(debug_files)} files <= 20 limit"
                )

        except Exception as e:
            activity.logger.debug(
                f"[LLMManager._cleanup_old_debug_files] Cleanup failed: {type(e).__name__}: {str(e)}"
            )
            activity.logger.warning(f"Failed to cleanup old debug files: {str(e)}")
