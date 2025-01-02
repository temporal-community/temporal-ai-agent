import asyncio
import json

from temporalio.client import Client
from workflows.tool_workflow import ToolWorkflow


async def main():
    # Create client connected to server at the given address
    client = await Client.connect("localhost:7233")
    workflow_id = "agent-workflow"

    handle = client.get_workflow_handle(workflow_id)

    # Queries the workflow for the conversation history
    tool_data = await handle.query(ToolWorkflow.get_tool_data)

    # pretty print
    print(json.dumps(tool_data, indent=4))


if __name__ == "__main__":
    asyncio.run(main())
