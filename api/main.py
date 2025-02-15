from fastapi import FastAPI
from typing import Optional
from temporalio.client import Client
from temporalio.exceptions import TemporalError
from temporalio.api.enums.v1 import WorkflowExecutionStatus

from workflows.agent_goal_workflow import AgentGoalWorkflow
from models.data_types import CombinedInput, AgentGoalWorkflowParams
from tools.goal_registry import goal_match_train_invoice
from fastapi.middleware.cors import CORSMiddleware
from shared.config import get_temporal_client, TEMPORAL_TASK_QUEUE

app = FastAPI()
temporal_client: Optional[Client] = None


@app.on_event("startup")
async def startup_event():
    global temporal_client
    temporal_client = await get_temporal_client()


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
    try:
        # Get workflow handle
        handle = temporal_client.get_workflow_handle("agent-workflow")

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
    try:
        handle = temporal_client.get_workflow_handle("agent-workflow")

        status_names = {
            WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_TERMINATED: "WORKFLOW_EXECUTION_STATUS_TERMINATED",
            WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_CANCELED: "WORKFLOW_EXECUTION_STATUS_CANCELED",
            WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_FAILED: "WORKFLOW_EXECUTION_STATUS_FAILED",
        }

        failed_states = [
            WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_TERMINATED,
            WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_CANCELED,
            WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_FAILED,
        ]

        # Check workflow status first
        description = await handle.describe()
        if description.status in failed_states:
            status_name = status_names.get(description.status, "UNKNOWN_STATUS")
            print(f"Workflow is in {status_name} state. Returning empty history.")
            return []

        # Only query if workflow is running
        conversation_history = await handle.query("get_conversation_history")
        return conversation_history

    except TemporalError as e:
        print(f"Temporal error: {e}")
        return []


@app.post("/send-prompt")
async def send_prompt(prompt: str):
    # Create combined input
    combined_input = CombinedInput(
        tool_params=AgentGoalWorkflowParams(None, None),
        agent_goal=goal_match_train_invoice,
    )

    workflow_id = "agent-workflow"

    # Start (or signal) the workflow
    await temporal_client.start_workflow(
        AgentGoalWorkflow.run,
        combined_input,
        id=workflow_id,
        task_queue=TEMPORAL_TASK_QUEUE,
        start_signal="user_prompt",
        start_signal_args=[prompt],
    )

    return {"message": f"Prompt '{prompt}' sent to workflow {workflow_id}."}


@app.post("/confirm")
async def send_confirm():
    """Sends a 'confirm' signal to the workflow."""
    workflow_id = "agent-workflow"
    handle = temporal_client.get_workflow_handle(workflow_id)
    await handle.signal("confirm")
    return {"message": "Confirm signal sent."}


@app.post("/end-chat")
async def end_chat():
    """Sends a 'end_chat' signal to the workflow."""
    workflow_id = "agent-workflow"

    try:
        handle = temporal_client.get_workflow_handle(workflow_id)
        await handle.signal("end_chat")
        return {"message": "End chat signal sent."}
    except TemporalError as e:
        print(e)
        # Workflow not found; return an empty response
        return {}


@app.post("/start-workflow")
async def start_workflow():
    # Create combined input
    combined_input = CombinedInput(
        tool_params=AgentGoalWorkflowParams(None, None),
        agent_goal=goal_match_train_invoice,
    )

    workflow_id = "agent-workflow"

    # Start the workflow with the starter prompt from the goal
    await temporal_client.start_workflow(
        AgentGoalWorkflow.run,
        combined_input,
        id=workflow_id,
        task_queue=TEMPORAL_TASK_QUEUE,
        start_signal="user_prompt",
        start_signal_args=["### " + goal_match_train_invoice.starter_prompt],
    )

    return {
        "message": f"Workflow started with goal's starter prompt: {goal_match_train_invoice.starter_prompt}."
    }
