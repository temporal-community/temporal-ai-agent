import asyncio

import concurrent.futures

from temporalio.worker import Worker

from activities.tool_activities import dynamic_tool_activity

from shared.config import get_temporal_client, TEMPORAL_LEGACY_TASK_QUEUE


async def main():
    # Create the client
    client = await get_temporal_client()

    # Run the worker
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as activity_executor:
        worker = Worker(
            client,
            task_queue=TEMPORAL_LEGACY_TASK_QUEUE,
            activities=[
                dynamic_tool_activity,
            ],
            activity_executor=activity_executor,
        )

        print(f"Starting legacy worker, connecting to task queue: {TEMPORAL_LEGACY_TASK_QUEUE}")
        await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
