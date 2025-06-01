import asyncio
import multiprocessing
import sys
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from temporalio.client import Client
from temporalio.testing import WorkflowEnvironment

# Due to https://github.com/python/cpython/issues/77906, multiprocessing on
# macOS starting with Python 3.8 has changed from "fork" to "spawn". For
# pre-3.8, we are changing it for them.
if sys.version_info < (3, 8) and sys.platform.startswith("darwin"):
    multiprocessing.set_start_method("spawn", True)


def pytest_addoption(parser):
    parser.addoption(
        "--workflow-environment",
        default="local",
        help="Which workflow environment to use ('local', 'time-skipping', or target to existing server)",
    )


@pytest.fixture(scope="session")
def event_loop():
    # See https://github.com/pytest-dev/pytest-asyncio/issues/68
    # See https://github.com/pytest-dev/pytest-asyncio/issues/257
    # Also need ProactorEventLoop on older versions of Python with Windows so
    # that asyncio subprocess works properly
    if sys.version_info < (3, 8) and sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def env(request) -> AsyncGenerator[WorkflowEnvironment, None]:
    env_type = request.config.getoption("--workflow-environment")
    if env_type == "local":
        env = await WorkflowEnvironment.start_local(
            dev_server_extra_args=[
                "--dynamic-config-value",
                "frontend.enableExecuteMultiOperation=true",
            ]
        )
    elif env_type == "time-skipping":
        env = await WorkflowEnvironment.start_time_skipping()
    else:
        env = WorkflowEnvironment.from_client(await Client.connect(env_type))
    yield env
    await env.shutdown()


@pytest_asyncio.fixture
async def client(env: WorkflowEnvironment) -> Client:
    return env.client


@pytest.fixture
def sample_agent_goal():
    """Sample agent goal for testing."""
    from models.tool_definitions import AgentGoal, ToolArgument, ToolDefinition

    return AgentGoal(
        id="test_goal",
        category_tag="test",
        agent_name="TestAgent",
        agent_friendly_description="A test agent for testing purposes",
        description="Test goal for agent testing",
        tools=[
            ToolDefinition(
                name="TestTool",
                description="A test tool for testing purposes",
                arguments=[
                    ToolArgument(
                        name="test_arg", type="string", description="A test argument"
                    )
                ],
            )
        ],
    )


@pytest.fixture
def sample_conversation_history():
    """Sample conversation history for testing."""
    return {
        "messages": [
            {"actor": "user", "response": "Hello, I need help with testing"},
            {"actor": "agent", "response": "I can help you with that"},
        ]
    }


@pytest.fixture
def sample_combined_input(sample_agent_goal):
    """Sample combined input for workflow testing."""
    from collections import deque

    from models.data_types import AgentGoalWorkflowParams, CombinedInput

    tool_params = AgentGoalWorkflowParams(
        conversation_summary="Test conversation summary",
        prompt_queue=deque(),  # Start with empty queue for most tests
    )

    return CombinedInput(agent_goal=sample_agent_goal, tool_params=tool_params)
