import asyncio

import concurrent.futures

from temporalio.worker import Worker

from activities.tool_activities import ToolActivities, dynamic_tool_activity
from workflows.tool_workflow import ToolWorkflow

from shared.config import get_temporal_client, TEMPORAL_TASK_QUEUE


async def main():
    # Create the client
    client = await get_temporal_client()

    activities = ToolActivities()

    # Run the worker
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as activity_executor:
        worker = Worker(
            client,
            task_queue=TEMPORAL_TASK_QUEUE,
            workflows=[ToolWorkflow],
            activities=[
                activities.prompt_llm,
                activities.validate_llm_prompt,
                dynamic_tool_activity,
            ],
            activity_executor=activity_executor,
        )

        print(f"Starting worker, connecting to task queue: {TEMPORAL_TASK_QUEUE}")
        await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
