import asyncio
import sys

from temporalio.client import Client
from workflows import EntityOllamaWorkflow


async def main():
    # Create client connected to server at the given address
    client = await Client.connect("localhost:7233")

    workflow_id = "entity-ollama-workflow"

    handle = client.get_workflow_handle_for(EntityOllamaWorkflow.run, workflow_id)

    # Sends a signal to the workflow
    await handle.signal(EntityOllamaWorkflow.end_chat)


if __name__ == "__main__":
    print("Sending signal to end chat.")
    asyncio.run(main())
