import asyncio
import concurrent.futures
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from activities.tool_activities import ToolActivities, dynamic_tool_activity
from workflows.tool_workflow import ToolWorkflow


async def main():
    # Create client connected to server at the given address
    client = await Client.connect("localhost:7233")
    activities = ToolActivities()

    # Run the worker
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as activity_executor:
        worker = Worker(
            client,
            task_queue="ollama-task-queue",
            workflows=[ToolWorkflow],
            activities=[
                activities.prompt_llm,
                activities.parse_tool_data,
                activities.validate_and_parse_json,
                dynamic_tool_activity,
            ],
            activity_executor=activity_executor,
        )
        await worker.run()


if __name__ == "__main__":
    print("Starting worker")
    print("Then run 'python send_message.py \"<prompt>\"'")

    logging.basicConfig(level=logging.INFO)

    asyncio.run(main())
