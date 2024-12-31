import asyncio
import sys

from temporalio.client import Client
from workflows import OllamaParams, EntityOllamaWorkflow


async def main(prompt):
    # Create client connected to server at the given address
    client = await Client.connect("localhost:7233")

    workflow_id = "entity-ollama-workflow"

    # Sends a signal to the workflow (and starts it if needed)
    await client.start_workflow(
        EntityOllamaWorkflow.run,
        OllamaParams(None, None),  # or pass in custom summary/prompt_queue if desired
        id=workflow_id,
        task_queue="ollama-task-queue",
        start_signal="user_prompt",
        start_signal_args=[prompt],
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python send_message.py '<prompt>'")
        print("Example: python send_message.py 'What animals are marsupials?'")
    else:
        asyncio.run(main(sys.argv[1]))
