from fastapi import FastAPI
from temporalio.client import Client
from workflows.tool_workflow import ToolWorkflow
from models.data_types import CombinedInput, ToolsData, ToolWorkflowParams
from temporalio.exceptions import TemporalError
from fastapi.middleware.cors import CORSMiddleware
from tools.tool_registry import (
    find_events_tool,
    search_flights_tool,
    create_invoice_tool,
)


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

    # Build the ToolsData
    tools_data = ToolsData(
        tools=[find_events_tool, search_flights_tool, create_invoice_tool],
        description="Help the user gather args for these tools in order: "
        "1. FindEvents: Find an event to travel to "
        "2. SearchFlights: search for a flight around the event dates "
        "3. GenerateInvoice: Create a simple invoice for the cost of that flight ",
        example_conversation_history="\n ".join(
            [
                "user: I'd like to travel to an event",
                "agent: Sure! Let's start by finding an event you'd like to attend. Could you tell me which city and month you're interested in?",
                "user: In Sao Paulo, Brazil, in February",
                "agent: Great! Let's find an events in Sao Paulo, Brazil in February.",
                "user_confirmed_tool_run: <user clicks confirm on FindEvents tool>",
                "tool_result: { 'event_name': 'Carnival', 'event_date': '2023-02-25' }",
                "agent: Found an event! There's Carnival on 2023-02-25, ending on 2023-02-28. Would you like to search for flights around these dates?",
                "user: Yes, please",
                "agent: Let's search for flights around these dates. Could you provide your departure city?",
                "user: New York",
                "agent: Thanks, searching for flights from New York to Sao Paulo around 2023-02-25 to 2023-02-28.",
                "user_confirmed_tool_run: <user clicks confirm on SearchFlights tool>"
                'tool_result: results including {"flight_number": "CX101", "return_flight_number": "CX102", "price": 850.0}',
                "agent: Found some flights! The cheapest is CX101 for $850. Would you like to generate an invoice for this flight?",
                "user_confirmed_tool_run: <user clicks confirm on CreateInvoice tool>",
                'tool_result: { "status": "success", "invoice": { "flight_number": "CX101", "amount": 850.0 }, invoiceURL: "https://example.com/invoice" }',
                "agent: Invoice generated! Here's the link: https://example.com/invoice",
            ]
        ),
    )

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
