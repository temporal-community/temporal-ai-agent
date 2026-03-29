"""
LLM Manager with automatic fallback support using Temporal activity heartbeat for state persistence.

Environment Variables:
    LLM_MODEL: Primary LLM model (e.g., "openai/gpt-4")
    LLM_KEY: API key for primary LLM
    LLM_BASE_URL: Optional custom base URL for primary LLM
    LLM_TIMEOUT_SECONDS: Timeout for primary LLM calls in seconds (default: 10)
    LLM_FALLBACK_MODEL: Fallback LLM model
    LLM_FALLBACK_KEY: API key for fallback LLM
    LLM_FALLBACK_BASE_URL: Optional custom base URL for fallback LLM
    LLM_FALLBACK_TIMEOUT_SECONDS: Timeout for fallback LLM calls in seconds (default: 10)
    LLM_DEBUG_OUTPUT: Enable debug file output ("true"/"false", default: "false")
    LLM_DEBUG_OUTPUT_DIR: Directory for debug files (default: "./debug_llm_calls")

Usage:
    manager = LLMManager()
    response = await manager.call_llm([{"role": "user", "content": "Hello"}])

"""
import asyncio
import os
import json
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv
from litellm import completion
from temporalio import activity

load_dotenv(override=True)


class LLMManager:
    """
    Manages LLM calls with intelligence to use the primary LLM or fallback.
    """

    def __init__(self):
        """Initialize LLM Manager with primary and fallback configurations."""
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
        else:
            print(f"  No fallback model configured")

        if self.debug_output_enabled:
            print(f"  Debug output enabled: {self.debug_output_dir}")
        else:
            print(f"  Debug output disabled")

        print(f"  Initial state: using_fallback=False, primary_failure_time=None")

    async def call_llm(self, messages: List[Dict[str, str]], fallback_mode: bool) -> Dict[str, Any]:
        """
        Call LLM with automatic fallback support.

        Args:
            messages: The messages to send to the LLM

        Returns:
            The LLM response

        Raises:
            Exception: If LLM call fails
        """

        await self._handle_debug(messages)

        # Determine which LLM
        if fallback_mode:
            response = await self._call_fallback_llm(messages)
        else:
            # Try primary LLM and throw exception on failure
            response = await self._call_primary_llm_strict(messages)

        return response

    async def _call_primary_llm_strict(
        self, messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Call the primary LLM and throw exception on failure.

        :param messages: LLM messages
        :return: LLM response
        :raises: Exception if primary LLM fails
        """
        activity.logger.debug(
            f"[LLMManager._call_primary_llm_strict] Attempting primary LLM call: {self.primary_model}"
        )
        completion_kwargs = {
            "model": self.primary_model,
            "messages": messages,
            "api_key": self.primary_key,
        }

        if self.primary_base_url:
            completion_kwargs["base_url"] = self.primary_base_url

        response = completion(
            **completion_kwargs, timeout=self.primary_timeout_seconds
        )
        activity.logger.info(f"Primary LLM call successful: {self.primary_model}")

        return response


    async def _call_fallback_llm(
        self, messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Call the fallback LLM."""
        if not self.fallback_model:
            raise Exception("No fallback model configured")

        activity.logger.info(f"Using fallback LLM: {self.fallback_model}")

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
            activity.logger.info(f"Fallback LLM call successful: {self.fallback_model}")
            return response
        except Exception as fallback_error:
            activity.logger.error(f"Fallback LLM also failed: {str(fallback_error)}")
            raise Exception(
                f"Fallback LLM failed. "
                f"Primary: {self.primary_model}, Fallback: {self.fallback_model}"
            )

    async def _handle_debug(self, messages: List[Dict[str, str]]):
        """
        Handle debug output if enabled.
        """
        activity.logger.debug(
            f"[LLMManager.call_llm] Starting LLM call with {len(messages)} messages"
        )

        # Save debug output if enabled
        if self.debug_output_enabled:
            await self._save_debug_output(messages)

    async def _save_debug_output(self, messages: List[Dict[str, str]]) -> None:
        """
        Save LLM messages in a format that can be cut/pasted into an LLM interface.
        """
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
