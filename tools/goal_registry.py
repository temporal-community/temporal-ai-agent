from typing import List
from models.tool_definitions import AgentGoal
import tools.tool_registry as tool_registry

# Turn on Silly Mode - this should be a description of the persona you'd like the bot to have and can be a single word or a phrase.
# Example if you want the bot to be a specific person, like Mario or Christopher Walken, or to describe a specific tone:
#SILLY_MODE="Christopher Walken"
#SILLY_MODE="belligerent"
# 
# Example if you want it to take on a persona (include 'a'):
#SILLY_MODE="a pirate"
# Note - this only works with certain LLMs. Grok for sure will stay in character, while OpenAI will not.
SILLY_MODE="off"
if SILLY_MODE is not None and SILLY_MODE != "off":
    silly_prompt = "You are " + SILLY_MODE +", stay in character at all times. "
    print("Silly mode is on: " + SILLY_MODE)
else:
    silly_prompt = ""

starter_prompt_generic = silly_prompt + "Welcome me, give me a description of what you can do, then ask me for the details you need to do your job."

goal_choose_agent_type = AgentGoal(
    id = "goal_choose_agent_type",
    category_tag="agent_selection",
    agent_name="Choose Agent",
    agent_friendly_description="Choose the type of agent to assist you today.",
    tools=[
        tool_registry.list_agents_tool, 
        tool_registry.change_goal_tool,
    ],
    description="The user wants to choose which type of agent they will interact with. "
        "Help the user gather args for these tools, in order: "
        "1. ListAgents: List agents available to interact with. Do not ask for user confirmation for this tool. "
        "2. ChangeGoal: Change goal of agent "
        "After these tools are complete, change your goal to the new goal as chosen by the user. ",
    starter_prompt=starter_prompt_generic + " Begin by listing all details of all agents as provided by the output of the first tool included in this goal. ",
    example_conversation_history="\n ".join(
        [
            "agent: Here are the currently available agents.",
            "user_confirmed_tool_run: <user clicks confirm on ListAgents tool>",
            "tool_result: { 'agent_name': 'Event Flight Finder', 'goal_id': 'goal_event_flight_invoice', 'agent_description': 'Helps users find interesting events and arrange travel to them' }",
            "agent: The available agents are: 1. Event Flight Finder. \n Which agent would you like to speak to? (You can respond with name or number.)",
            "user: 1, Event Flight Finder",
            "user_confirmed_tool_run: <user clicks confirm on ChangeGoal tool>",
            "tool_result: { 'new_goal': 'goal_event_flight_invoice' }",
        ]
    ),
)

# Easter egg - if silly mode = a pirate, include goal_pirate_treasure as a "system" goal so it always shows up.
# Can also turn make this goal available by setting the GOAL_CATEGORIES in the env file to include 'pirate', but if SILLY_MODE
#   is not 'a pirate', the interaction as a whole will be less pirate-y.
pirate_category_tag = "pirate"
if SILLY_MODE == "a pirate":
    pirate_category_tag = "system"
goal_pirate_treasure = AgentGoal(
    id = "goal_pirate_treasure",
    category_tag=pirate_category_tag,
    agent_name="Arrr, Find Me Treasure!",
    agent_friendly_description="Sail the high seas and find me pirate treasure, ye land lubber!",
    tools=[
        tool_registry.give_hint_tool,
        tool_registry.guess_location_tool,
    ],
    description="The user wants to find a pirate treasure. "
        "Help the user gather args for these tools, in a loop, until treasure_found is True or the user requests to be done: "
        "1. GiveHint: If the user wants a hint regarding the location of the treasure, give them a hint. If they do not want a hint, this tool is optional."
        "2. GuessLocation: The user guesses where the treasure is, by giving an address. ",
    starter_prompt=starter_prompt_generic,
    example_conversation_history="\n ".join(
        [
            "user: I'd like to try to find the treasure",
            "agent: Sure! Do you want a hint?",
            "user: yes",
            "agent: Here is hint number 1!",
            "user_confirmed_tool_run: <user clicks confirm on GiveHint tool>",
            "tool_result: { 'hint_number': 1, 'hint': 'The treasure is in the state of Arizona.' }",
            "agent: The treasure is in the state of Arizona. Would you like to guess the address of the treasure? ",
            "user: Yes, address is 123 Main St Phoenix, AZ",
            "agent: Let's see if you found the treasure...",
            "user_confirmed_tool_run: <user clicks confirm on GuessLocation tool>"
            "tool_result: {'treasure_found':False}",
            "agent: Nope, that's not the right location! Do you want another hint?",
            "user: yes",
            "agent: Here is hint number 2.",
            "user_confirmed_tool_run: <user clicks confirm on GiveHint tool>",
            "tool_result: { 'hint_number': 2, 'hint': 'The treasure is in the city of Tucson, AZ.' }",
            "agent: The treasure is in the city of Tucson, AZ. Would you like to guess the address of the treasure? ",
            "user: Yes, address is 456 Main St Tucson, AZ",
            "agent: Let's see if you found the treasure...",
            "user_confirmed_tool_run: <user clicks confirm on GuessLocation tool>",
            "tool_result: {'treasure_found':True}",
            "agent: Congratulations, Land Lubber, you've found the pirate treasure!",
        ]
    ),
)

goal_match_train_invoice = AgentGoal(
    id = "goal_match_train_invoice",
    category_tag="travel-trains",
    agent_name="UK Premier League Match Trip Booking",
    agent_friendly_description="Book a trip to a city in the UK around the dates of a premier league match.",
    tools=[
        tool_registry.search_fixtures_tool,
        tool_registry.search_trains_tool,
        tool_registry.book_trains_tool,
        tool_registry.create_invoice_tool,
    ],
    description="The user wants to book a trip to a city in the UK around the dates of a premier league match. "
    "Help the user find a premier league match to attend, search and book trains for that match and offers to invoice them for the cost of train tickets. "
    "The user lives in London. "
    "Gather args for these tools in order, ensuring you move the user from one tool to the next: "
    "1. SearchFixtures: Search for fixtures for a team within a specified date range. The user might ask questions about the matches dates and locations to decide on where to go. "
    "2. SearchTrains: Search for trains to the city of the match and list them for the customer to choose from "
    "3. BookTrains: Book the train tickets, used to invoice the user for the cost of the train tickets "
    "4. CreateInvoice: Invoices the user for the cost of train tickets, with total and details inferred from the conversation history ",
    starter_prompt=starter_prompt_generic,
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
            "agent: Great! I've generated your invoice for your trains to the Manchester City match on the 10th of May. You can view and pay your invoice at this link: https://invoice.stripe.com/i/acct_1NBOLuKVZbzw7QA5/test_YWNjdF8xTkJPTHVLVlpienc3UUE1LF9SbGJlZ2xLMjhlc3lxNzFkVVBXbkswOUlFa2Rna1RxLDEzMDAwMTY4Nw0200RLeJRMlw?s=ap <this is the end of the chat>",
        ]
    ),
)

goal_event_flight_invoice = AgentGoal(
    id = "goal_event_flight_invoice",
    category_tag="travel-flights",
    agent_name="Australia and New Zealand Event Flight Booking",
    agent_friendly_description="Book a trip to a city in Australia or New Zealand around the dates of events in that city.",    
    tools=[
        tool_registry.find_events_tool,
        tool_registry.search_flights_tool,
        tool_registry.create_invoice_tool,
    ],
    description="Help the user gather args for these tools in order: "
    "1. FindEvents: Find an event to travel to "
    "2. SearchFlights: search for a flight around the event dates "
    "3. CreateInvoice: Create a simple invoice for the cost of that flight ",
    starter_prompt=starter_prompt_generic,
    example_conversation_history="\n ".join(
        [
            "user: I'd like to travel to an event",
            "agent: Sure! Let's start by finding an event you'd like to attend. I know about events in Australia and New Zealand cities. Could you tell me which city and month you're interested in?",
            "user: sydney in may please",
            "agent: Great! Let's find an events in Sydney in May.",
            "user_confirmed_tool_run: <user clicks confirm on FindEvents tool>",
            "tool_result: { 'event_name': 'Vivid Sydney', 'event_date': '2023-05-01' }",
            "agent: Found an event! There's Vivid Sydney on May 1 2025, ending on May 14 2025. Would you like to search for flights around these dates?",
            "user: Yes, please",
            "agent: Let's search for flights around these dates. Could you provide your departure city?",
            "user: San Francisco",
            "agent: Thanks, searching for flights from San Francisco to Sydney around 2023-02-25 to 2023-02-28.",
            "user_confirmed_tool_run: <user clicks confirm on SearchFlights tool>"
            'tool_result: results including {"flight_number": "CX101", "return_flight_number": "CX102", "price": 850.0}',
            "agent: Found some flights! The cheapest is CX101 for $850. Would you like to generate an invoice for this flight?",
            "user_confirmed_tool_run: <user clicks confirm on CreateInvoice tool>",
            'tool_result: { "status": "success", "invoice": { "flight_number": "CX101", "amount": 850.0 }, invoiceURL: "https://example.com/invoice" }',
            "agent: Invoice generated! Here's the link: https://example.com/invoice",
        ]
    ),
)

# This goal uses the data/employee_pto_data.json file as dummy data.
goal_hr_schedule_pto = AgentGoal(
    id = "goal_hr_schedule_pto",
    category_tag="hr",
    agent_name="Schedule PTO",
    agent_friendly_description="Schedule PTO based on your available PTO.",   
    tools=[
        tool_registry.current_pto_tool,
        tool_registry.future_pto_calc_tool,
        tool_registry.book_pto_tool,
    ],
    description="The user wants to schedule paid time off (PTO) after today's date. To assist with that goal, help the user gather args for these tools in order: "
    "1. CurrentPTO: Tell the user how much PTO they currently have "
    "2. FuturePTOCalc: Tell the user how much PTO they will have as of the prospective future date "
    "3. BookPTO: Book PTO after user types 'yes'",
    starter_prompt=starter_prompt_generic,
    example_conversation_history="\n ".join(
        [
            "user: I'd like to schedule some time off",
            "agent: Sure! Let's start by determining how much PTO you currently have. May I have your email address?",
            "user: bob.johnson@emailzzz.com",
            "agent: Great! I can tell you how much PTO you currently have accrued.",
            "user_confirmed_tool_run: <user clicks confirm on CurrentPTO tool>",
            "tool_result: { 'num_hours': 400, 'num_days': 50 }",
            "agent: You have 400 hours, or 50 days, of PTO available. What dates would you like to take your time off? ",
            "user: Dec 1 through Dec 5",
            "agent: Let's check if you'll have enough PTO accrued by Dec 1 of this year to accomodate that.",
            "user_confirmed_tool_run: <user clicks confirm on FuturePTO tool>"
            'tool_result: {"enough_pto": True, "pto_hrs_remaining_after": 410}',
            "agent: You do in fact have enough PTO to accommodate that, and will have 410 hours remaining after you come back. Do you want to book the PTO? ",
            "user: yes ",
            "user_confirmed_tool_run: <user clicks confirm on BookPTO tool>",
            'tool_result: { "status": "success" }',
            "agent: PTO successfully booked! ",
        ]
    ),
)

# This goal uses the data/employee_pto_data.json file as dummy data.
goal_hr_check_pto = AgentGoal(
    id = "goal_hr_check_pto",
    category_tag="hr",
    agent_name="Check PTO Amount",
    agent_friendly_description="Check your available PTO.",   
    tools=[
        tool_registry.current_pto_tool,
    ],
    description="The user wants to check their paid time off (PTO) after today's date. To assist with that goal, help the user gather args for these tools in order: "
    "1. CurrentPTO: Tell the user how much PTO they currently have ",
    starter_prompt=starter_prompt_generic,
    example_conversation_history="\n ".join(
        [
            "user: I'd like to check my time off amounts at the current time",
            "agent: Sure! I can help you out with that. May I have your email address?",
            "user: bob.johnson@emailzzz.com",
            "agent: Great! I can tell you how much PTO you currently have accrued.",
            "user_confirmed_tool_run: <user clicks confirm on CurrentPTO tool>",
            "tool_result: { 'num_hours': 400, 'num_days': 50 }",
            "agent: You have 400 hours, or 50 days, of PTO available.",
        ]
    ),
)

# check integration with bank
goal_hr_check_paycheck_bank_integration_status = AgentGoal(
    id = "goal_hr_check_paycheck_bank_integration_status",
    category_tag="hr",
    agent_name="Check paycheck deposit status",
    agent_friendly_description="Check your integration between your employer and your financial institution.",   
    tools=[
        tool_registry.paycheck_bank_integration_status_check,
    ],
    description="The user wants to check their bank integration used to deposit their paycheck. To assist with that goal, help the user gather args for these tools in order: "
    "1. CheckPayBankStatus: Tell the user the status of their paycheck bank integration ",
    starter_prompt=starter_prompt_generic,
    example_conversation_history="\n ".join(
        [
            "user: I'd like to check paycheck bank integration",
            "agent: Sure! I can help you out with that. May I have your email address?",
            "user: bob.johnson@emailzzz.com",
            "agent: Great! I can tell you what the status is for your paycheck bank integration.",
            "user_confirmed_tool_run: <user clicks confirm on CheckPayBankStatus tool>",
            "tool_result: { 'status': connected }",
            "agent: Your paycheck bank deposit integration is properly connected.",
        ]
    ),
)

# this tool checks account balances, and uses ./data/customer_account_data.json as dummy data
goal_fin_check_account_balances = AgentGoal(
    id = "goal_fin_check_account_balances",
    category_tag="fin",
    agent_name="Check balances",
    agent_friendly_description="Check your account balances in Checking, Savings, etc.",   
    tools=[
        tool_registry.financial_check_account_is_valid,
        tool_registry.financial_get_account_balances,
    ],
    description="The user wants to check their account balances at the bank or financial institution. To assist with that goal, help the user gather args for these tools in order: "
    "1. FinCheckAccountIsValid: validate the user's account is valid"
    "2. FinCheckAccountBalance: Tell the user their account balance at the bank or financial institution",
    starter_prompt=starter_prompt_generic,
    example_conversation_history="\n ".join(
        [
            "user: I'd like to check my account balances",
            "agent: Sure! I can help you out with that. May I have your email address or account number?",
            "user: email is bob.johnson@emailzzz.com ",
            "user_confirmed_tool_run: <user clicks confirm on FincheckAccountIsValid tool>",
            "tool_result: { 'status': account valid }",
            "agent: Great! I can tell you what the your account balances are.",
            "user_confirmed_tool_run: <user clicks confirm on FinCheckAccountBalance tool>",
            "tool_result: { 'name': Matt Murdock, 'email': matt.murdock@nelsonmurdock.com, 'account_id': 11235, 'checking_balance': 875.40, 'savings_balance': 3200.15, 'bitcoin_balance': 0.1378, 'account_creation_date': 2014-03-10 }",
            "agent: Your account balances are as follows: \n "
                "Checking: $875.40. \n "
                "Savings: $3200.15. \n "
                "Bitcoint: 0.1378 \n "
                "Thanks for being a customer since 2014!",
        ]
    ),
)

# this tool checks account balances, and uses ./data/customer_account_data.json as dummy data
goal_fin_move_money = AgentGoal(
    id = "goal_fin_move_money",
    category_tag="fin",
    agent_name="Money Order",
    agent_friendly_description="Initiate a money movement order.",   
    tools=[
        tool_registry.financial_check_account_is_valid,
        tool_registry.financial_get_account_balances,
        tool_registry.financial_move_money,
    ],
    description="The user wants to transfer money in their account at the bank or financial institution. To assist with that goal, help the user gather args for these tools in order: "
    "1. FinCheckAccountIsValid: validate the user's account is valid"
    "2. FinCheckAccountBalance: Tell the user their account balance at the bank or financial institution"
    "3. FinMoveMoney: Initiate a money movement order",
    starter_prompt=starter_prompt_generic,
    example_conversation_history="\n ".join(
        [
            "user: I'd like transfer some money",
            "agent: Sure! I can help you out with that. May I have account number and email address?",
            "user: account number is 11235813",
            "user_confirmed_tool_run: <user clicks confirm on FincheckAccountIsValid tool>",
            "tool_result: { 'status': account valid }",
            "agent: Great! Here are your account balances:",
            "user_confirmed_tool_run: <user clicks confirm on FinCheckAccountBalance tool>", 
            "tool_result: { 'name': Matt Murdock, 'email': matt.murdock@nelsonmurdock.com, 'account_id': 11235, 'checking_balance': 875.40, 'savings_balance': 3200.15, 'bitcoin_balance': 0.1378, 'account_creation_date': 2014-03-10 }",
            "agent: Your account balances are as follows: \n "
                "Checking: $875.40. \n "
                "Savings: $3200.15. \n "
                "Bitcoint: 0.1378 \n "
            "agent: how much would you like to move, from which account type, and to which account number?",
            "user: I'd like to move $500 from savings to account number #56789",
            "user_confirmed_tool_run: <user clicks confirm on FinMoveMoney tool>",
            "tool_result: { 'status': money movement complete, 'confirmation id': 333421, 'new_balance': $2700.15 }",
            "agent: Money movement order completed! New account balance: $2700.15. Your confirmation id is 333421. "
        ]
    ),
)

#Add the goals to a list for more generic processing, like listing available agents
goal_list: List[AgentGoal] = []
goal_list.append(goal_choose_agent_type)
goal_list.append(goal_pirate_treasure)
goal_list.append(goal_event_flight_invoice)
goal_list.append(goal_match_train_invoice)
goal_list.append(goal_hr_schedule_pto)
goal_list.append(goal_hr_check_pto)
goal_list.append(goal_hr_check_paycheck_bank_integration_status)
goal_list.append(goal_fin_check_account_balances)
goal_list.append(goal_fin_move_money)



