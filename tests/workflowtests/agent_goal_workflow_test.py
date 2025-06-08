import concurrent.futures
import uuid
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Sequence

from temporalio import activity
from temporalio.client import Client, WorkflowExecutionStatus
from temporalio.common import RawValue
from temporalio.worker import Worker

from api.main import get_initial_agent_goal
from models.data_types import (
    AgentGoalWorkflowParams,
    CombinedInput,
    EnvLookupInput,
    EnvLookupOutput,
    ToolPromptInput,
    ValidationInput,
    ValidationResult,
)
from models.tool_definitions import MCPServerDefinition
from workflows.agent_goal_workflow import AgentGoalWorkflow


@contextmanager
def my_context():
    print("Setup")
    yield "some_value"  # Value assigned to 'as' variable
    print("Cleanup")


async def test_flight_booking(client: Client):
    # load_dotenv("test_flights_single.env")

    with my_context() as value:
        print(f"Working with {value}")

        # Create the test environment
        # env = await WorkflowEnvironment.start_local()
        # client = env.client
        task_queue_name = str(uuid.uuid4())
        workflow_id = str(uuid.uuid4())

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

        @activity.defn(name="mcp_list_tools")
        async def mock_mcp_list_tools(
            server_definition: MCPServerDefinition,
            include_tools: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            return {"success": True, "tools": {}, "server_name": "test"}

        @activity.defn(name="mcp_tool_activity")
        async def mock_mcp_tool_activity(
            tool_name: str, tool_args: Dict[str, Any]
        ) -> Dict[str, Any]:
            return {"success": True, "result": "Mock MCP tool result"}

        @activity.defn(name="dynamic_tool_activity", dynamic=True)
        async def mock_dynamic_tool_activity(args: Sequence[RawValue]) -> dict:
            return {"success": True, "result": "Mock dynamic tool result"}

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=100
        ) as activity_executor:
            worker = Worker(
                client,
                task_queue=task_queue_name,
                workflows=[AgentGoalWorkflow],
                activities=[
                    mock_get_wf_env_vars,
                    mock_agent_validatePrompt,
                    mock_agent_toolPlanner,
                    mock_mcp_list_tools,
                    mock_mcp_tool_activity,
                    mock_dynamic_tool_activity,
                ],
                activity_executor=activity_executor,
            )

            async with worker:
                initial_agent_goal = get_initial_agent_goal()
                # Create combined input
                combined_input = CombinedInput(
                    tool_params=AgentGoalWorkflowParams(None, None),
                    agent_goal=initial_agent_goal,
                )

                prompt = "Hello!"

                # async with Worker(client, task_queue=task_queue_name, workflows=[AgentGoalWorkflow], activities=[ToolActivities.agent_validatePrompt, ToolActivities.agent_toolPlanner, dynamic_tool_activity]):

                # todo set goal categories for scenarios
                handle = await client.start_workflow(
                    AgentGoalWorkflow.run,
                    combined_input,
                    id=workflow_id,
                    task_queue=task_queue_name,
                    start_signal="user_prompt",
                    start_signal_args=[prompt],
                )
                # todo send signals to simulate user input
                # await handle.signal(AgentGoalWorkflow.user_prompt, "book flights") # for multi-goal
                await handle.signal(
                    AgentGoalWorkflow.user_prompt, "sydney in september"
                )
                assert (
                    WorkflowExecutionStatus.RUNNING == (await handle.describe()).status
                )

                # assert ["Hello, user1", "Hello, user2"] == await handle.result()
                await handle.signal(
                    AgentGoalWorkflow.user_prompt, "I'm all set, end conversation"
                )

                # assert WorkflowExecutionStatus.COMPLETED == (await handle.describe()).status

                result = await handle.result()
                print(f"Workflow result: {result}")
                # todo dump workflow history for analysis optional
                # todo assert result is good
