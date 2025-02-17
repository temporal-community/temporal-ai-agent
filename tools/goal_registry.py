from models.tool_definitions import AgentGoal
from tools.tool_registry import (
    search_fixtures_tool,
    search_flights_tool,
    search_trains_tool,
    book_trains_tool,
    create_invoice_tool,
)

goal_match_train_invoice = AgentGoal(
    tools=[
        search_fixtures_tool,
        search_trains_tool,
        book_trains_tool,
        create_invoice_tool,
    ],
    description="The user wants to book a trip to a city in the UK around the dates of a premier league match. "
    "Help the user find a premier league match to attend, search and book trains for that match and offers to invoice them for the cost of train tickets. "
    "The user lives in London. "
    "Gather args for these tools in order, ensuring you move the user from one tool to the next: "
    "1. SearchFixtures: Search for fixtures for a team within a specified date range. The user might ask questions about the matches dates and locations to decide on where to go. "
    "2. SearchTrains: Search for trains to the city of the match and list them for the customer to choose from "
    "3. BookTrains: Book the train tickets, used to invoice the user for the cost of the train tickets "
    "4. CreateInvoice: Invoices the user for the cost of train tickets, with total and details inferred from the conversation history ",
    starter_prompt="Welcome me, give me a description of what you can do, then ask me for the details you need to begin your job as an agent ",
    example_conversation_history="\n ".join(
        [
            "user: I'd like to travel to a premier league match",
            "agent: Sure! Let's start by finding a match you'd like to attend. I know about Premier League fixtures in the UK. Could you tell me which team and what date range you're interested in?"
            "user: Wolves between mid-April and the first week of May, please."
            "agent: Great! Let's find fixtures for Wolverhampton Wanderers FC between 2025-04-15 and 2025-05-05."
            "user_confirmed_tool_run: <user clicks confirm on SearchFixtures tool, passing the full team name as an input>",
            'tool_result: SearchFixtures responds in this JSON format and the results are parsed by the agent below {"fixtures": [{"awayTeam": "West Ham United FC","date": "2025-04-01","homeTeam": "Wolverhampton Wanderers FC"},...,'
            "agent: I found 4 Wolves matches in May 2025: 1. Man City vs Wolves (Away) - May 3 2. Wolves vs Brighton (Home) - May 10 3. Crystal Palace vs Wolves (Away) - May 18 4. Wolves vs Brentford (Home) - May 25 Which match would you like to attend? I'll help you find trains from London.",
            "user: How about the Man City match",
            "agent: Great! Let's find trains to Manchester and back for the match.",
            "user_confirmed_tool_run: <user clicks confirm on SearchTrains tool>",
            'tool_result: SearchTrains responds in this JSON format and the results are parsed by the agent below: {"journeys": [{"arrival": "Manchester","arrival_time": "2025-04-18T12:11","departure": "London","departure_time": "2025-04-18T11:00","id": "T8049","platform": "1","price": 73.5,"type": "outbound"},',
            "agent: I found several train options for your journey to Manchester including outbound options on May 9 at 11am, 3:30pm and 4:30pm and return options on May 11 at 9am, 11am and 1pm. Which trains would you like to book?",
            "user: I'd like the 11am outbound and 3:30pm return",
            "agent: Sounds good, let's book train tickets for the 11am outbound and 3:30pm return trains on May 9 and May 11, one day before and after the match.",
            "user_confirmed_tool_run: <user clicks confirm on BookTrains tool>",
            'tool_result: BookTrains responds in this JSON format and the results are parsed by the agent belowg [{"booking_reference": "BR10879","journey_id": "T9532,T1027","status": "confirmed"}]',
            "agent: Your train tickets have been booked with the reference ABCD1234. Are you ready to be invoiced for the total cost of the train tickets?",
            "user: Yes, pelase invoice me.",
            "user_confirmed_tool_run: <user clicks confirm on CreateInvoice tool which includes details of the train journey, the match, and the total cost>",
            'tool_result: CreateInvoice responds in this JSON format and the results are parsed by the agent below (including a link to the invoice): {"invoiceStatus": "open","invoiceURL": "https://invoice.stripe.com/i/acct_1NBOLuKVZbzw7QA5/test_YWNjdF8xTkJPTHVLVlpienc3UUE1LF9SbGJlZ2xLMjhlc3lxNzFkVVBXbkswOUlFa2Rna1RxLDEzMDAwMTY4Nw0200RLeJRMlw?s=ap","reference": "F9B01CD7-0001"}',
            "agent: Great! I've generated your invoice for your trains to the Manchester City match on the 10th of May. You can view and pay your invoice at this link: https://invoice.stripe.com/i/acct_1NBOLuKVZbzw7QA5/test_YWNjdF8xTkJPTHVLVlpienc3UUE1LF9SbGJlZ2xLMjhlc3lxNzFkVVBXbkswOUlFa2Rna1RxLDEzMDAwMTY4Nw0200RLeJRMlw?s=ap",
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
            "agent: Train tickets booked! Would you like me to create an invoice for the flights and train tickets?",
            "user_confirmed_tool_run: <user clicks confirm on CreateInvoice tool>",
            'tool_result: { "status": "success", "invoice": { "flight_number": "CX101", "amount": 850.0 }, invoiceURL: "https://example.com/invoice" }',
            "agent: Invoice generated! Here's the link: https://example.com/invoice",
        ]
    ),
)
