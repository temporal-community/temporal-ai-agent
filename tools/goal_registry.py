from models.tool_definitions import AgentGoal
from tools.tool_registry import (
    find_events_tool,
    search_flights_tool,
    create_invoice_tool,
)

goal_event_flight_invoice = AgentGoal(
    tools=[find_events_tool, search_flights_tool, create_invoice_tool],
    description="Help the user gather args for these tools in order: "
    "1. FindEvents: Find an event to travel to "
    "2. SearchFlights: search for a flight around the event dates "
    "3. CreateInvoice: Create a simple invoice for the cost of that flight ",
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
