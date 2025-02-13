from models.tool_definitions import AgentGoal
from tools.tool_registry import (
    search_fixtures_tool,
    search_flights_tool,
    search_trains_tool,
    book_train_tool,
    create_invoice_tool,
)

goal_match_train_invoice = AgentGoal(
    tools=[
        search_fixtures_tool,
        search_trains_tool,
        book_train_tool,
        create_invoice_tool,
    ],
    description="Help the user book trains to a premier league match. The user lives in London. Gather args for these tools in order: "
    "1. SearchFixtures: Search for fixtures for a team in a given month"
    "2. SearchTrains: Search for trains to the city of the match and list them for the customer to choose from"
    "3. BookTrain: Book the train tickets"
    "4. CreateInvoice: Proactively offer to create a simple invoice for the cost of the flights and train tickets",
    starter_prompt="Welcome me, give me a description of what you can do, then ask me for the details you need to do your job",
    example_conversation_history="\n ".join(
        [
            "user: I'd like to travel to a premier league match",
            "agent: Sure! Let's start by finding an match you'd like to attend. I know about Premier League fixtures in the UK. Could you tell me which team and month you're interested in?",
            "user: Wolves in May please",
            "agent: Great! Let's find a match for Wolverhampton Wanderers FC in May.",
            "user_confirmed_tool_run: <user clicks confirm on SearchFixtures tool, passing the full team name as an input>",
            'tool_result: results including {"homeTeam": "Wolverhampton Wanderers FC", "awayTeam": "Manchester United", "date": "2025-05-04"}',
            "agent: Found a match! <agent provides a human-readable list of match options including the location and date>",
            "user_confirmed_tool_run: <user clicks confirm on SearchTrains tool>",
            "tool_result: <results including train dates and times, origin and depature stations>",
            "agent: Found some trains! <agent provides a human-readable list of train options>",
            "user_confirmed_tool_run: <user clicks confirm on BookTrain tool>",
            'tool_result: results including {"status": "success"}',
            "agent: Train tickets booked! Please confirm the following invoice for the journey. <agent infers total amount for the invoice and details from the conversation history>",
            "user_confirmed_tool_run: <user clicks confirm on CreateInvoice tool which includes details of the train journey, the match, and the total cost>",
            "tool_result: contains an invoiceURL",
            "agent: Great! I've generated your invoice for your trains to the <match>. You can view and pay your invoice at this link: https://invoice.stripe.com/i/acct_1NBOLuKVZbzw7QA5/test_YWNjdF8xTkJPTHVLVlpienc3UUE1LF9SaHlBTU9GYnFibEJ4VlpNaThkWkhrcUR6a1dwTmNULDEyOTE2MjkwNA0200CCUNvTox?s=ap",
        ]
    ),
)

# unused
goal_event_flight_invoice = AgentGoal(
    tools=[
        search_fixtures_tool,
        search_flights_tool,
        search_trains_tool,
        create_invoice_tool,
    ],
    description="Help the user gather args for these tools in order: "
    "1. SearchFixtures: Search for fixtures for a team in a given month"
    "2. SearchFlights: Search for a flight around the match dates"
    "3. SearchTrains: Search for trains to visit somewhere before or after the match"
    "4. BookTrain: Book the train tickets"
    "5. CreateInvoice: Create a simple invoice for the cost of the flights and train tickets",
    starter_prompt="Welcome me, give me a description of what you can do, then ask me for the details you need to do your job",
    example_conversation_history="\n ".join(
        [
            "user: I'd like to travel to a football match",
            "agent: Sure! Let's start by finding an match you'd like to attend. I know about Premier League fixtures in the UK. Could you tell me which team and month you're interested in?",
            "user: Wolves in May please",
            "agent: Great! Let's find a match for Wolverhampton Wanderers FC in May.",
            "user_confirmed_tool_run: <user clicks confirm on SearchFixtures tool, passing the full team name as an input>",
            'tool_result: results including {"homeTeam": "Wolverhampton Wanderers FC", "awayTeam": "Manchester United", "date": "2025-05-04"}',
            "agent: Found a match! There's an away game against Manchester United on May 4 2025. Would you like to search for flights around this date?",
            "user: Yes, please",
            "agent: Let's search for flights around this date. Could you provide your departure city?",
            "user: San Francisco",
            "agent: Thanks, searching for flights from San Francisco to the Manchester around 2025-05-03 to 2025-05-05.",
            "user_confirmed_tool_run: <user clicks confirm on SearchFlights tool>"
            'tool_result: results including {"flight_number": "CX101", "return_flight_number": "CX102", "price": 850.0}',
            "agent: Found some flights! The cheapest is CX101 for $850. Would you like to go for this one?",
            "user: Yes, please",
            "agent: Great! So you're flying to the city the match is in, anywhere else you'd like to visit while you're there?",
            "user: I'd like to visit my friend in Edinburgh after the match",
            "agent: Got it! Let's search for trains from Manchester to Edinburgh and back.",
            "user_confirmed_tool_run: <user clicks confirm on SearchTrains tool>",
            'tool_result: results including {"train_number": "T1234", "price": 30.0}',
            "agent: Found these train options! The cheapest is T1234 for $30. Would you like to go for this one?",
            "user: Yes, please",
            "agent: Great, lets book the train tickets",
            "user_confirmed_tool_run: <user clicks confirm on BookTrain tool>",
            'tool_result: results including {"status": "success"}',
            "agent: Train tickets booked! Now let's create an invoice for the flights and train tickets",
            "user_confirmed_tool_run: <user clicks confirm on CreateInvoice tool>",
            'tool_result: { "status": "success", "invoice": { "flight_number": "CX101", "amount": 850.0 }, invoiceURL: "https://example.com/invoice" }',
            "agent: Invoice generated! Here's the link: https://example.com/invoice",
        ]
    ),
)
