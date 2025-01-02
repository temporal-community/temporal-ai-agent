import asyncio
import sys
from temporalio.client import Client


async def main():

    # 1) Connect to Temporal and signal the workflow
    client = await Client.connect("localhost:7233")

    workflow_id = "agent-workflow"

    await client.get_workflow_handle(workflow_id).signal("confirm")


if __name__ == "__main__":
    if len(sys.argv) != 1:
        print("Usage: python send_confirm.py'")
    else:
        asyncio.run(main())
