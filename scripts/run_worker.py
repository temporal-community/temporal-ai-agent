import asyncio
import concurrent.futures
import os
from dotenv import load_dotenv

from temporalio.worker import Worker

from activities.tool_activities import ToolActivities, dynamic_tool_activity
from workflows.agent_goal_workflow import AgentGoalWorkflow

from shared.config import get_temporal_client, TEMPORAL_TASK_QUEUE


async def main():
    # Load environment variables
    load_dotenv(override=True)
    
    # Print LLM configuration info
    llm_provider = os.environ.get("LLM_PROVIDER", "openai").lower()
    print(f"Worker will use LLM provider: {llm_provider}")
    
    # Create the client
    client = await get_temporal_client()

    # Initialize the activities class once with the specified LLM provider
    activities = ToolActivities()
    print(f"ToolActivities initialized with LLM provider: {llm_provider}")

    # Run the worker
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as activity_executor:
        worker = Worker(
            client,
            task_queue=TEMPORAL_TASK_QUEUE,
            workflows=[AgentGoalWorkflow],
            activities=[
                activities.agent_validatePrompt,
                activities.agent_toolPlanner,
                dynamic_tool_activity,
            ],
            activity_executor=activity_executor,
        )

        print(f"Starting worker, connecting to task queue: {TEMPORAL_TASK_QUEUE}")
        await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
