import asyncio
import sys

from shared.config import get_temporal_client


async def main():

    # Connect to Temporal and signal the workflow
    client = await get_temporal_client()

    workflow_id = "agent-workflow"

    await client.get_workflow_handle(workflow_id).signal("confirm")


if __name__ == "__main__":
    if len(sys.argv) != 1:
        print("Usage: python send_confirm.py'")
    else:
        asyncio.run(main())
