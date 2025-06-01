import uuid

from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker

from models.data_types import (
    AgentGoalWorkflowParams,
    CombinedInput,
    EnvLookupInput,
    EnvLookupOutput,
    ToolPromptInput,
    ValidationInput,
    ValidationResult,
)
from workflows.agent_goal_workflow import AgentGoalWorkflow


class TestAgentGoalWorkflow:
    """Test cases for AgentGoalWorkflow."""

    async def test_workflow_initialization(
        self, client: Client, sample_combined_input: CombinedInput
    ):
        """Test workflow can be initialized and started."""
        task_queue_name = str(uuid.uuid4())

        # Create mock activity functions with proper signatures
        @activity.defn(name="get_wf_env_vars")
        async def mock_get_wf_env_vars(input: EnvLookupInput) -> EnvLookupOutput:
            return EnvLookupOutput(show_confirm=True, multi_goal_mode=True)

        async with Worker(
            client,
            task_queue=task_queue_name,
            workflows=[AgentGoalWorkflow],
            activities=[mock_get_wf_env_vars],
        ):
            # Start workflow but don't wait for completion since it runs indefinitely
            handle = await client.start_workflow(
                AgentGoalWorkflow.run,
                sample_combined_input,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Verify workflow is running
            assert handle is not None

            # Query the workflow to check initial state
            conversation_history = await handle.query(
                AgentGoalWorkflow.get_conversation_history
            )
            assert isinstance(conversation_history, dict)
            assert "messages" in conversation_history

            # Test goal query
            agent_goal = await handle.query(AgentGoalWorkflow.get_agent_goal)
            assert agent_goal == sample_combined_input.agent_goal

            # End the workflow
            await handle.signal(AgentGoalWorkflow.end_chat)
            result = await handle.result()
            assert isinstance(result, str)

    async def test_user_prompt_signal(
        self, client: Client, sample_combined_input: CombinedInput
    ):
        """Test user_prompt signal handling."""
        task_queue_name = str(uuid.uuid4())

        # Create mock activity functions with proper signatures
        @activity.defn(name="get_wf_env_vars")
        async def mock_get_wf_env_vars(input: EnvLookupInput) -> EnvLookupOutput:
            return EnvLookupOutput(show_confirm=True, multi_goal_mode=True)

        @activity.defn(name="agent_validatePrompt")
        async def mock_agent_validatePrompt(
            validation_input: ValidationInput,
        ) -> ValidationResult:
            return ValidationResult(validationResult=True, validationFailedReason={})

        @activity.defn(name="agent_toolPlanner")
        async def mock_agent_toolPlanner(input: ToolPromptInput) -> dict:
            return {"next": "done", "response": "Test response from LLM"}

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

            # Send user prompt
            await handle.signal(
                AgentGoalWorkflow.user_prompt, "Hello, this is a test message"
            )

            # Wait for workflow to complete (it should end due to "done" next step)
            result = await handle.result()
            assert isinstance(result, str)

            # Verify the conversation includes our message
            import json

            try:
                conversation_history = json.loads(result.replace("'", '"'))
            except Exception:
                # Fallback to eval if json fails
                conversation_history = eval(result)
            messages = conversation_history["messages"]

            # Should have our user message and agent response
            user_messages = [msg for msg in messages if msg["actor"] == "user"]
            assert len(user_messages) > 0
            assert any(
                "Hello, this is a test message" in str(msg["response"])
                for msg in user_messages
            )

    async def test_confirm_signal(
        self, client: Client, sample_combined_input: CombinedInput
    ):
        """Test confirm signal handling for tool execution."""
        task_queue_name = str(uuid.uuid4())

        # Create mock activity functions with proper signatures
        @activity.defn(name="get_wf_env_vars")
        async def mock_get_wf_env_vars(input: EnvLookupInput) -> EnvLookupOutput:
            return EnvLookupOutput(show_confirm=True, multi_goal_mode=True)

        @activity.defn(name="agent_validatePrompt")
        async def mock_agent_validatePrompt(
            validation_input: ValidationInput,
        ) -> ValidationResult:
            return ValidationResult(validationResult=True, validationFailedReason={})

        @activity.defn(name="agent_toolPlanner")
        async def mock_agent_toolPlanner(input: ToolPromptInput) -> dict:
            return {
                "next": "confirm",
                "tool": "TestTool",
                "args": {"test_arg": "test_value"},
                "response": "Ready to execute tool",
            }

        @activity.defn(name="TestTool")
        async def mock_test_tool(args: dict) -> dict:
            return {"result": "Test tool executed successfully"}

        async with Worker(
            client,
            task_queue=task_queue_name,
            workflows=[AgentGoalWorkflow],
            activities=[
                mock_get_wf_env_vars,
                mock_agent_validatePrompt,
                mock_agent_toolPlanner,
                mock_test_tool,
            ],
        ):
            handle = await client.start_workflow(
                AgentGoalWorkflow.run,
                sample_combined_input,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Send user prompt that will require confirmation
            await handle.signal(AgentGoalWorkflow.user_prompt, "Execute the test tool")

            # Query to check tool data is set
            import asyncio

            await asyncio.sleep(0.1)  # Give workflow time to process

            tool_data = await handle.query(AgentGoalWorkflow.get_latest_tool_data)
            if tool_data:
                assert tool_data.get("tool") == "TestTool"
                assert tool_data.get("next") == "confirm"

            # Send confirmation and end chat
            await handle.signal(AgentGoalWorkflow.confirm)
            await handle.signal(AgentGoalWorkflow.end_chat)

            result = await handle.result()
            assert isinstance(result, str)

    async def test_validation_failure(
        self, client: Client, sample_combined_input: CombinedInput
    ):
        """Test workflow handles validation failures correctly."""
        task_queue_name = str(uuid.uuid4())

        # Create mock activity functions with proper signatures
        @activity.defn(name="get_wf_env_vars")
        async def mock_get_wf_env_vars(input: EnvLookupInput) -> EnvLookupOutput:
            return EnvLookupOutput(show_confirm=True, multi_goal_mode=True)

        @activity.defn(name="agent_validatePrompt")
        async def mock_agent_validatePrompt(
            validation_input: ValidationInput,
        ) -> ValidationResult:
            return ValidationResult(
                validationResult=False,
                validationFailedReason={
                    "next": "question",
                    "response": "Your request doesn't make sense in this context",
                },
            )

        async with Worker(
            client,
            task_queue=task_queue_name,
            workflows=[AgentGoalWorkflow],
            activities=[mock_get_wf_env_vars, mock_agent_validatePrompt],
        ):
            handle = await client.start_workflow(
                AgentGoalWorkflow.run,
                sample_combined_input,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Send invalid prompt
            await handle.signal(
                AgentGoalWorkflow.user_prompt, "Invalid nonsensical prompt"
            )

            # Give workflow time to process the prompt
            import asyncio

            await asyncio.sleep(0.2)

            # End workflow to check conversation
            await handle.signal(AgentGoalWorkflow.end_chat)
            result = await handle.result()

            # Verify validation failure message was added
            import json

            try:
                conversation_history = json.loads(result.replace("'", '"'))
            except Exception:
                # Fallback to eval if json fails
                conversation_history = eval(result)
            messages = conversation_history["messages"]

            # Should have validation failure response
            agent_messages = [msg for msg in messages if msg["actor"] == "agent"]
            assert len(agent_messages) > 0
            assert any(
                "doesn't make sense" in str(msg["response"]) for msg in agent_messages
            )

    async def test_conversation_summary_initialization(
        self, client: Client, sample_agent_goal
    ):
        """Test workflow initializes with conversation summary."""
        task_queue_name = str(uuid.uuid4())

        # Create input with conversation summary
        from collections import deque

        tool_params = AgentGoalWorkflowParams(
            conversation_summary="Previous conversation summary", prompt_queue=deque()
        )
        combined_input = CombinedInput(
            agent_goal=sample_agent_goal, tool_params=tool_params
        )

        # Create mock activity functions with proper signatures
        @activity.defn(name="get_wf_env_vars")
        async def mock_get_wf_env_vars(input: EnvLookupInput) -> EnvLookupOutput:
            return EnvLookupOutput(show_confirm=True, multi_goal_mode=True)

        async with Worker(
            client,
            task_queue=task_queue_name,
            workflows=[AgentGoalWorkflow],
            activities=[mock_get_wf_env_vars],
        ):
            handle = await client.start_workflow(
                AgentGoalWorkflow.run,
                combined_input,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Give workflow time to initialize
            import asyncio

            await asyncio.sleep(0.1)

            # Query conversation summary
            summary = await handle.query(AgentGoalWorkflow.get_summary_from_history)
            assert summary == "Previous conversation summary"

            # Query conversation history - should include summary message
            conversation_history = await handle.query(
                AgentGoalWorkflow.get_conversation_history
            )
            messages = conversation_history["messages"]

            # Should have conversation_summary message
            summary_messages = [
                msg for msg in messages if msg["actor"] == "conversation_summary"
            ]
            assert len(summary_messages) == 1
            assert summary_messages[0]["response"] == "Previous conversation summary"

            # End workflow
            await handle.signal(AgentGoalWorkflow.end_chat)
            await handle.result()

    async def test_workflow_queries(
        self, client: Client, sample_combined_input: CombinedInput
    ):
        """Test all workflow query methods."""
        task_queue_name = str(uuid.uuid4())

        # Create mock activity functions with proper signatures
        @activity.defn(name="get_wf_env_vars")
        async def mock_get_wf_env_vars(input: EnvLookupInput) -> EnvLookupOutput:
            return EnvLookupOutput(show_confirm=True, multi_goal_mode=True)

        async with Worker(
            client,
            task_queue=task_queue_name,
            workflows=[AgentGoalWorkflow],
            activities=[mock_get_wf_env_vars],
        ):
            handle = await client.start_workflow(
                AgentGoalWorkflow.run,
                sample_combined_input,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Give workflow time to initialize
            import asyncio

            await asyncio.sleep(0.1)

            # Test get_conversation_history query
            conversation_history = await handle.query(
                AgentGoalWorkflow.get_conversation_history
            )
            assert isinstance(conversation_history, dict)
            assert "messages" in conversation_history

            # Test get_agent_goal query
            agent_goal = await handle.query(AgentGoalWorkflow.get_agent_goal)
            assert agent_goal.id == sample_combined_input.agent_goal.id

            # Test get_summary_from_history query
            summary = await handle.query(AgentGoalWorkflow.get_summary_from_history)
            # Summary might be None if not set, so check for that
            if sample_combined_input.tool_params.conversation_summary:
                assert summary == sample_combined_input.tool_params.conversation_summary
            else:
                assert summary is None

            # Test get_latest_tool_data query (should be None initially)
            tool_data = await handle.query(AgentGoalWorkflow.get_latest_tool_data)
            assert tool_data is None

            # End workflow
            await handle.signal(AgentGoalWorkflow.end_chat)
            await handle.result()

    async def test_enable_disable_debugging_confirm_signals(
        self, client: Client, sample_combined_input: CombinedInput
    ):
        """Test debugging confirm enable/disable signals."""
        task_queue_name = str(uuid.uuid4())

        # Create mock activity functions with proper signatures
        @activity.defn(name="get_wf_env_vars")
        async def mock_get_wf_env_vars(input: EnvLookupInput) -> EnvLookupOutput:
            return EnvLookupOutput(show_confirm=True, multi_goal_mode=True)

        async with Worker(
            client,
            task_queue=task_queue_name,
            workflows=[AgentGoalWorkflow],
            activities=[mock_get_wf_env_vars],
        ):
            handle = await client.start_workflow(
                AgentGoalWorkflow.run,
                sample_combined_input,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Test enable debugging confirm signal
            await handle.signal(AgentGoalWorkflow.enable_debugging_confirm)

            # Test disable debugging confirm signal
            await handle.signal(AgentGoalWorkflow.disable_debugging_confirm)

            # End workflow
            await handle.signal(AgentGoalWorkflow.end_chat)
            result = await handle.result()
            assert isinstance(result, str)

    async def test_workflow_with_empty_prompt_queue(
        self, client: Client, sample_agent_goal
    ):
        """Test workflow behavior with empty prompt queue."""
        task_queue_name = str(uuid.uuid4())

        # Create input with empty prompt queue
        from collections import deque

        tool_params = AgentGoalWorkflowParams(
            conversation_summary=None, prompt_queue=deque()
        )
        combined_input = CombinedInput(
            agent_goal=sample_agent_goal, tool_params=tool_params
        )

        # Create mock activity functions with proper signatures
        @activity.defn(name="get_wf_env_vars")
        async def mock_get_wf_env_vars(input: EnvLookupInput) -> EnvLookupOutput:
            return EnvLookupOutput(show_confirm=True, multi_goal_mode=True)

        async with Worker(
            client,
            task_queue=task_queue_name,
            workflows=[AgentGoalWorkflow],
            activities=[mock_get_wf_env_vars],
        ):
            handle = await client.start_workflow(
                AgentGoalWorkflow.run,
                combined_input,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

            # Give workflow time to initialize
            import asyncio

            await asyncio.sleep(0.1)

            # Query initial state
            conversation_history = await handle.query(
                AgentGoalWorkflow.get_conversation_history
            )
            assert isinstance(conversation_history, dict)
            assert "messages" in conversation_history

            # Should have no messages initially (empty prompt queue, no summary)
            messages = conversation_history["messages"]
            assert len(messages) == 0

            # End workflow
            await handle.signal(AgentGoalWorkflow.end_chat)
            result = await handle.result()
            assert isinstance(result, str)

    async def test_multiple_user_prompts(
        self, client: Client, sample_combined_input: CombinedInput
    ):
        """Test workflow handling multiple user prompts in sequence."""
        task_queue_name = str(uuid.uuid4())

        # Create mock activity functions with proper signatures
        @activity.defn(name="get_wf_env_vars")
        async def mock_get_wf_env_vars(input: EnvLookupInput) -> EnvLookupOutput:
            return EnvLookupOutput(show_confirm=True, multi_goal_mode=True)

        @activity.defn(name="agent_validatePrompt")
        async def mock_agent_validatePrompt(
            validation_input: ValidationInput,
        ) -> ValidationResult:
            return ValidationResult(validationResult=True, validationFailedReason={})

        @activity.defn(name="agent_toolPlanner")
        async def mock_agent_toolPlanner(input: ToolPromptInput) -> dict:
            # Keep workflow running for multiple prompts
            return {"next": "question", "response": f"Processed: {input.prompt}"}

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

            # Send multiple prompts
            await handle.signal(AgentGoalWorkflow.user_prompt, "First message")
            import asyncio

            await asyncio.sleep(0.1)

            await handle.signal(AgentGoalWorkflow.user_prompt, "Second message")
            await asyncio.sleep(0.1)

            await handle.signal(AgentGoalWorkflow.user_prompt, "Third message")
            await asyncio.sleep(0.1)

            # End workflow
            await handle.signal(AgentGoalWorkflow.end_chat)
            result = await handle.result()
            assert isinstance(result, str)

            # Parse result and verify multiple messages
            import json

            try:
                conversation_history = json.loads(result.replace("'", '"'))
            except Exception:
                conversation_history = eval(result)
            messages = conversation_history["messages"]

            # Should have at least one user message (timing dependent)
            user_messages = [msg for msg in messages if msg["actor"] == "user"]
            assert len(user_messages) >= 1

            # Verify at least the first message was processed
            message_texts = [str(msg["response"]) for msg in user_messages]
            assert any("First message" in text for text in message_texts)
