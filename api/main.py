from fastapi import FastAPI
from temporalio.client import Client
from workflows.tool_workflow import ToolWorkflow
from models.data_types import CombinedInput, ToolsData, ToolWorkflowParams
from tools.tool_registry import all_tools

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Temporal AI Agent!"}


@app.get("/tool-data")
async def get_tool_data():
    """Calls the workflow's 'get_tool_data' query."""
    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle("agent-workflow")
    tool_data = await handle.query(ToolWorkflow.get_tool_data)
    return tool_data


@app.post("/send-prompt")
async def send_prompt(prompt: str):
    client = await Client.connect("localhost:7233")

    # Build the ToolsData
    tools_data = ToolsData(tools=all_tools)

    # Create combined input
    combined_input = CombinedInput(
        tool_params=ToolWorkflowParams(None, None),
        tools_data=tools_data,
    )

    workflow_id = "agent-workflow"

    # Start (or signal) the workflow
    await client.start_workflow(
        ToolWorkflow.run,
        combined_input,
        id=workflow_id,
        task_queue="agent-task-queue",
        start_signal="user_prompt",
        start_signal_args=[prompt],
    )

    return {"message": f"Prompt '{prompt}' sent to workflow {workflow_id}."}


@app.post("/confirm")
async def send_confirm():
    """Sends a 'confirm' signal to the workflow."""
    client = await Client.connect("localhost:7233")
    workflow_id = "agent-workflow"
    handle = client.get_workflow_handle(workflow_id)
    await handle.signal("confirm")
    return {"message": "Confirm signal sent."}
