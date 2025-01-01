import asyncio
import sys

from temporalio.client import Client

from models.data_types import CombinedInput, ToolsData, ToolWorkflowParams
from models.tool_definitions import ToolDefinition, ToolArgument
from workflows.tool_workflow import ToolWorkflow


async def main(prompt):
    # Construct your tool definitions in code
    search_flights_tool = ToolDefinition(
        name="SearchFlights",
        description="Search for return flights from an origin to a destination within a date range",
        arguments=[
            ToolArgument(
                name="origin",
                type="string",
                description="Airport or city (infer airport code from city)",
            ),
            ToolArgument(
                name="destination",
                type="string",
                description="Airport or city code for arrival (infer airport code from city)",
            ),
            ToolArgument(
                name="dateDepart",
                type="ISO8601",
                description="Start of date range in human readable format",
            ),
            ToolArgument(
                name="dateReturn",
                type="ISO8601",
                description="End of date range in human readable format",
            ),
        ],
    )

    # Wrap it in ToolsData
    tools_data = ToolsData(tools=[search_flights_tool])

    combined_input = CombinedInput(
        tool_params=ToolWorkflowParams(None, None), tools_data=tools_data
    )

    # Create client connected to Temporal server
    client = await Client.connect("localhost:7233")

    workflow_id = "ollama-agent"

    # Start or signal the workflow, passing OllamaParams and tools_data
    await client.start_workflow(
        ToolWorkflow.run,
        combined_input,  # or pass custom summary/prompt_queue
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
