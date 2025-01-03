import asyncio
import sys
from temporalio.client import Client

from models.data_types import CombinedInput, ToolsData, ToolWorkflowParams
from tools.tool_registry import event_travel_tools
from workflows.tool_workflow import ToolWorkflow


async def main(prompt: str):
    # Build the ToolsData
    tools_data = ToolsData(
        tools=event_travel_tools,
        description="Helps the user find an event to travel to, search flights, and create an invoice for those flights.",
    )

    # 2) Create combined input
    combined_input = CombinedInput(
        tool_params=ToolWorkflowParams(None, None),
        tools_data=tools_data,
    )

    # 3) Connect to Temporal and start or signal the workflow
    client = await Client.connect("localhost:7233")
    workflow_id = "agent-workflow"

    await client.start_workflow(
        ToolWorkflow.run,
        combined_input,
        id=workflow_id,
        task_queue="agent-task-queue",
        start_signal="user_prompt",
        start_signal_args=[prompt],
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python send_message.py '<prompt>'")
        print("Example: python send_message.py 'I want an event in Oceania this March'")
    else:
        asyncio.run(main(sys.argv[1]))
