from fastapi import FastAPI
from temporalio.client import Client
from workflows.tool_workflow import ToolWorkflow
from models.data_types import CombinedInput, ToolWorkflowParams
from tools.goal_registry import goal_event_flight_invoice
from temporalio.exceptions import TemporalError
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Temporal AI Agent!"}


@app.get("/tool-data")
async def get_tool_data():
    """Calls the workflow's 'get_tool_data' query."""
    client = await Client.connect("localhost:7233")
    try:
        # Get workflow handle
        handle = client.get_workflow_handle("agent-workflow")

        # Check if the workflow is completed
        workflow_status = await handle.describe()
        if workflow_status.status == 2:
            # Workflow is completed; return an empty response
            return {}

        # Query the workflow
        tool_data = await handle.query("get_tool_data")
        return tool_data
    except TemporalError as e:
        # Workflow not found; return an empty response
        print(e)
        return {}


@app.get("/get-conversation-history")
async def get_conversation_history():
    """Calls the workflow's 'get_conversation_history' query."""
    client = await Client.connect("localhost:7233")
    try:
        handle = client.get_workflow_handle("agent-workflow")
        conversation_history = await handle.query("get_conversation_history")

        return conversation_history
    except TemporalError as e:
        print(e)
        return []


@app.post("/send-prompt")
async def send_prompt(prompt: str):
    client = await Client.connect("localhost:7233")

    # Create combined input
    combined_input = CombinedInput(
        tool_params=ToolWorkflowParams(None, None),
        agent_goal=goal_event_flight_invoice,
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


@app.post("/end-chat")
async def end_chat():
    """Sends a 'end_chat' signal to the workflow."""
    client = await Client.connect("localhost:7233")
    workflow_id = "agent-workflow"

    try:
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal("end_chat")
        return {"message": "End chat signal sent."}
    except TemporalError as e:
        print(e)
        # Workflow not found; return an empty response
        return {}
