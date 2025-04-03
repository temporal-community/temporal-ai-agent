import asyncio

from temporalio.client import Client, WorkflowExecutionStatus
from temporalio.worker import Worker
from temporalio.testing import TestWorkflowEnvironment
from api.main import get_initial_agent_goal
from models.data_types import AgentGoalWorkflowParams, CombinedInput
from workflows.agent_goal_workflow import AgentGoalWorkflow
from activities.tool_activities import ToolActivities, dynamic_tool_activity


async def asyncSetUp(self):
    # Set up the test environment
    self.env = await TestWorkflowEnvironment.create_local()

async def asyncTearDown(self):
    # Clean up after tests
    await self.env.shutdown()

async def test_flight_booking(client: Client):

    task_queue_name = "agent-ai-workflow"
    workflow_id = "agent-workflow"
    
    initial_agent_goal = get_initial_agent_goal()

    # Create combined input
    combined_input = CombinedInput(
        tool_params=AgentGoalWorkflowParams(None, None),
        agent_goal=initial_agent_goal,
    )

    workflow_id = "agent-workflow"
    async with Worker(client, task_queue=task_queue_name, workflows=[AgentGoalWorkflow], activities=[ToolActivities.agent_validatePrompt, ToolActivities.agent_toolPlanner, dynamic_tool_activity]):

        # todo set goal categories for scenarios
        handle = await client.start_workflow(
            AgentGoalWorkflow.run, id=workflow_id, task_queue=task_queue_name
        )
        # todo send signals based on 
        await handle.signal(AgentGoalWorkflow.user_prompt, "book flights")
        await handle.signal(AgentGoalWorkflow.user_prompt, "sydney in september")
        assert WorkflowExecutionStatus.RUNNING == (await handle.describe()).status

        
        #assert ["Hello, user1", "Hello, user2"] == await handle.result()
        await handle.signal(AgentGoalWorkflow.user_prompt, "I'm all set, end conversation")
        assert WorkflowExecutionStatus.COMPLETED == (await handle.describe()).status

   


    