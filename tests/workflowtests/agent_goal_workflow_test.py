from temporalio.client import Client, WorkflowExecutionStatus
from temporalio.worker import Worker
import concurrent.futures
from temporalio.testing import WorkflowEnvironment
from api.main import get_initial_agent_goal
from models.data_types import AgentGoalWorkflowParams, CombinedInput
from workflows.agent_goal_workflow import AgentGoalWorkflow
from activities.tool_activities import ToolActivities, dynamic_tool_activity
from unittest.mock import patch
from dotenv import load_dotenv
import os
from contextlib import contextmanager


@contextmanager
def my_context():
    print("Setup")
    yield "some_value"  # Value assigned to 'as' variable
    print("Cleanup")



async def test_flight_booking(client: Client):

    #load_dotenv("test_flights_single.env")
    
    with my_context() as value:
        print(f"Working with {value}")
    
        
        # Create the test environment
        #env = await WorkflowEnvironment.start_local()
        #client = env.client
        task_queue_name = "agent-ai-workflow"
        workflow_id = "agent-workflow"

        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as activity_executor:        
            worker = Worker(
                client, 
                task_queue=task_queue_name,
                workflows=[AgentGoalWorkflow],
                activities=[ToolActivities.agent_validatePrompt, ToolActivities.agent_toolPlanner, ToolActivities.get_wf_env_vars, dynamic_tool_activity],
                activity_executor=activity_executor,
            )

            async with worker:                 
                initial_agent_goal = get_initial_agent_goal()
                # Create combined input
                combined_input = CombinedInput(
                    tool_params=AgentGoalWorkflowParams(None, None),
                    agent_goal=initial_agent_goal,
                )

                prompt="Hello!"

                #async with Worker(client, task_queue=task_queue_name, workflows=[AgentGoalWorkflow], activities=[ToolActivities.agent_validatePrompt, ToolActivities.agent_toolPlanner, dynamic_tool_activity]):

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
                await handle.signal(AgentGoalWorkflow.user_prompt, "sydney in september")
                assert WorkflowExecutionStatus.RUNNING == (await handle.describe()).status

                
                #assert ["Hello, user1", "Hello, user2"] == await handle.result()
                await handle.signal(AgentGoalWorkflow.user_prompt, "I'm all set, end conversation")
                
                #assert WorkflowExecutionStatus.COMPLETED == (await handle.describe()).status

                result = await handle.result()
                #todo dump workflow history for analysis optional
                #todo assert result is good