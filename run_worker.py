import asyncio
import concurrent.futures
import logging

from temporalio.client import Client
from temporalio.worker import Worker
from workflows import EntityOllamaWorkflow

from activities import OllamaActivities


async def main():
    # Create client connected to server at the given address
    client = await Client.connect("localhost:7233")
    activities = OllamaActivities()

    # Run the worker
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as activity_executor:
        worker = Worker(
            client,
            task_queue="ollama-task-queue",
            workflows=[EntityOllamaWorkflow],
            activities=[activities.prompt_ollama],
            activity_executor=activity_executor,
        )
        await worker.run()


if __name__ == "__main__":
    print("Starting worker")
    print("Then run 'python send_message.py \"<prompt>\"'")

    logging.basicConfig(level=logging.INFO)

    asyncio.run(main())
