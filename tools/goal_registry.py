from models.tool_definitions import AgentGoal
from tools.tool_registry import (
    find_fixtures_tool,
    search_flights_tool,
    create_invoice_tool,
)

goal_event_flight_invoice = AgentGoal(
    tools=[find_fixtures_tool, search_flights_tool, create_invoice_tool],
    description="Help the user gather args for these tools in order: "
    "1. FindFixtures: Find fixtures for a team in a given month "
    "2. SearchFlights: search for a flight around the event dates "
    "3. CreateInvoice: Create a simple invoice for the cost of that flight ",
    example_conversation_history="\n ".join(
        [
            "user: I'd like to travel to a football match",
            "agent: Sure! Let's start by finding an match you'd like to attend. I know about Premier League fixtures in the UK. Could you tell me which team and month you're interested in?",
            "user: wolverhamptom in may please",
            "agent: Great! Let's find a match for Wolverhampton Wanderers in May.",
            "user_confirmed_tool_run: <user clicks confirm on FindFixtures tool>",
            'tool_result: results including {"homeTeam": "Wolverhampton Wanderers FC", "awayTeam": "Manchester United", "date": "2025-05-04"}',
            "agent: Found a match! There's an away game against Manchester United on May 4 2025. Would you like to search for flights around this date?",
            "user: Yes, please",
            "agent: Let's search for flights around this date. Could you provide your departure city?",
            "user: San Francisco",
            "agent: Thanks, searching for flights from San Francisco to the Manchester around 2025-05-03 to 2025-05-05.",
            "user_confirmed_tool_run: <user clicks confirm on SearchFlights tool>"
            'tool_result: results including {"flight_number": "CX101", "return_flight_number": "CX102", "price": 850.0}',
            "agent: Found some flights! The cheapest is CX101 for $850. Would you like to generate an invoice for this flight?",
            "user_confirmed_tool_run: <user clicks confirm on CreateInvoice tool>",
            'tool_result: { "status": "success", "invoice": { "flight_number": "CX101", "amount": 850.0 }, invoiceURL: "https://example.com/invoice" }',
            "agent: Invoice generated! Here's the link: https://example.com/invoice",
        ]
    ),
)
