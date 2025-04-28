from models.tool_definitions import ToolDefinition, ToolArgument

# ----- System tools -----
list_agents_tool = ToolDefinition(
    name="ListAgents",
    description="List available agents to interact with, pulled from goal_registry. ",
    arguments=[],
)

change_goal_tool = ToolDefinition(
    name="ChangeGoal",
    description="Change the goal of the active agent. ",
    arguments=[
        ToolArgument(
            name="goalID",
            type="string",
            description="Which goal to change to",
        ),
    ],
)

give_hint_tool = ToolDefinition(
    name="GiveHint",
    description="Give a hint to the user regarding the location of the pirate treasure. Use previous conversation to determine the hint_total, it should initially be 0 ",
    arguments=[
        ToolArgument(
            name="hint_total",
            type="number",
            description="How many hints have been given",
        ),
    ],
)

guess_location_tool = ToolDefinition(
    name="GuessLocation",
    description="Allow the user to guess the location (in the form of an address) of the pirate treasure. ",
    arguments=[
        ToolArgument(
            name="address",
            type="string",
            description="Address at which the user is guessing the treasure is located",
        ),
        ToolArgument(
            name="city",
            type="string",
            description="City at which the user is guessing the treasure is located",
        ),
        ToolArgument(
            name="state",
            type="string",
            description="State at which the user is guessing the treasure is located",
        ),
    ],
)

# ----- Travel use cases tools -----
search_flights_tool = ToolDefinition(
    name="SearchFlights",
    description="Search for return flights from an origin to a destination within a date range (dateDepart, dateReturn). "
    "You are allowed to suggest dates from the conversation history, but ALWAYS ask the user if ok.",
    arguments=[
        ToolArgument(
            name="origin",
            type="string",
            description="Airport or city (infer airport code from city and store)",
        ),
        ToolArgument(
            name="destination",
            type="string",
            description="Airport or city code for arrival (infer airport code from city and store)",
        ),
        ToolArgument(
            name="dateDepart",
            type="ISO8601",
            description="Start of date range in human readable format, when you want to depart",
        ),
        ToolArgument(
            name="dateReturn",
            type="ISO8601",
            description="End of date range in human readable format, when you want to return",
        ),
        ToolArgument(
            name="userConfirmation",
            type="string",
            description="Indication of the user's desire to search flights, and to confirm the details "
            + "before moving on to the next step",
        ),
    ],
)

search_trains_tool = ToolDefinition(
    name="SearchTrains",
    description="Search for trains between two English cities. Returns a list of train information for the user to choose from.",
    arguments=[
        ToolArgument(
            name="origin",
            type="string",
            description="The city or place to depart from",
        ),
        ToolArgument(
            name="destination",
            type="string",
            description="The city or place to arrive at",
        ),
        ToolArgument(
            name="outbound_time",
            type="ISO8601",
            description="The date and time to search for outbound trains. If time of day isn't asked for, assume a decent time of day/evening for the outbound journey",
        ),
        ToolArgument(
            name="return_time",
            type="ISO8601",
            description="The date and time to search for return trains. If time of day isn't asked for, assume a decent time of day/evening for the inbound journey",
        ),
    ],
)

book_trains_tool = ToolDefinition(
    name="BookTrains",
    description="Books train tickets. Returns a booking reference.",
    arguments=[
        ToolArgument(
            name="train_ids",
            type="string",
            description="The IDs of the trains to book, comma separated",
        ),
        ToolArgument(
            name="userConfirmation",
            type="string",
            description="Indication of user's desire to book train tickets",
        ),
    ],
)

create_invoice_tool = ToolDefinition(
    name="CreateInvoice",
    description="Generate an invoice for the items described for the total inferred by the conversation history so far. Returns URL to invoice.",
    arguments=[
        ToolArgument(
            name="amount",
            type="float",
            description="The total cost to be invoiced. Infer this from the conversation history.",
        ),
        ToolArgument(
            name="tripDetails",
            type="string",
            description="A description of the item details to be invoiced, inferred from the conversation history.",
        ),
        ToolArgument(
            name="userConfirmation",
            type="string",
            description="Indication of user's desire to create an invoice",
        ),
    ],
)

search_fixtures_tool = ToolDefinition(
    name="SearchFixtures",
    description="Search for upcoming fixtures for a given team within a date range inferred from the user's description. Valid teams this 24/25 season are Arsenal FC, Aston Villa FC, AFC Bournemouth, Brentford FC, Brighton & Hove Albion FC, Chelsea FC, Crystal Palace FC, Everton FC, Fulham FC, Ipswich Town FC, Leicester City FC, Liverpool FC, Manchester City FC, Manchester United FC, Newcastle United FC, Nottingham Forest FC, Southampton FC, Tottenham Hotspur FC, West Ham United FC, Wolverhampton Wanderers FC",
    arguments=[
        ToolArgument(
            name="team",
            type="string",
            description="The full name of the team to search for.",
        ),
        ToolArgument(
            name="date_from",
            type="string",
            description="The start date in format (YYYY-MM-DD) for the fixture search inferred from the user's request (e.g. mid-March).",
        ),
        ToolArgument(
            name="date_to",
            type="string",
            description="The end date in format (YYYY-MM-DD) for the fixture search (e.g. 'the last week of May').",
        ),
    ],
)

find_events_tool = ToolDefinition(
    name="FindEvents",
    description="Find upcoming events to travel to a given city (e.g., 'Melbourne') and a date or month. "
    "It knows about events in Oceania only (e.g. major Australian and New Zealand cities). "
    "It will search 1 month either side of the month provided. "
    "Returns a list of events. ",
    arguments=[
        ToolArgument(
            name="city",
            type="string",
            description="Which city to search for events",
        ),
        ToolArgument(
            name="month",
            type="string",
            description="The month to search for events (will search 1 month either side of the month provided)",
        ),
    ],
)

# ----- HR use cases tools -----
current_pto_tool = ToolDefinition(
    name="CurrentPTO",
    description="Find how much PTO a user currently has accrued. "
    "Returns the number of hours and (calculated) number of days of PTO. ",
    arguments=[
        ToolArgument(
            name="email",
            type="string",
            description="email address of user",
        ),
    ],
)

future_pto_calc_tool = ToolDefinition(
    name="FuturePTOCalc",
    description="Calculate if the user will have enough PTO as of their proposed date to accommodate the request. The proposed start and end dates should be in the future. "
    "Returns a boolean enough_pto and how many hours of PTO they will have remaining if they take the proposed dates. ",
    arguments=[
        ToolArgument(
            name="start_date",
            type="string",
            description="Start date of proposed PTO, sent in the form yyyy-mm-dd",
        ),
        ToolArgument(
            name="end_date",
            type="string",
            description="End date of proposed PTO, sent in the form yyyy-mm-dd",
        ),
        ToolArgument(
            name="email",
            type="string",
            description="email address of user",
        ),
    ],
)

book_pto_tool = ToolDefinition(
    name="BookPTO",
    description="Book PTO start and end date. Either 1) makes calendar item, or 2) sends calendar invite to self and boss? "
    "Returns a success indicator. ",
    arguments=[
        ToolArgument(
            name="start_date",
            type="string",
            description="Start date of proposed PTO, sent in the form yyyy-mm-dd",
        ),
        ToolArgument(
            name="end_date",
            type="string",
            description="End date of proposed PTO, sent in the form yyyy-mm-dd",
        ),
        ToolArgument(
            name="email",
            type="string",
            description="Email address of user, used to look up current PTO",
        ),
        ToolArgument(
            name="userConfirmation",
            type="string",
            description="Indication of user's desire to book PTO",
        ),
    ],
)

paycheck_bank_integration_status_check = ToolDefinition(
    name="CheckPayBankStatus",
    description="Check status of Bank Integration for Paychecks. "
    "Returns the status of the bank integration, connected or disconnected. ",
    arguments=[
        ToolArgument(
            name="email",
            type="string",
            description="email address of user",
        ),
    ],
)

# ----- Financial use cases tools -----
financial_check_account_is_valid = ToolDefinition(
    name="FinCheckAccountIsValid",
    description="Check if an account is valid by email address or account ID. "
    "Returns the account status, valid or invalid. ",
    arguments=[
        ToolArgument(
            name="email",
            type="string",
            description="email address of user",
        ),
        ToolArgument(
            name="account_id",
            type="string",
            description="account ID of user",
        ),
    ],
)

financial_get_account_balances = ToolDefinition(
    name="FinCheckAccountBalance",
    description="Get account balance for your accounts. "
    "Returns the account balances of your accounts. ",
    arguments=[
        ToolArgument(
            name="email_address_or_account_ID",
            type="string",
            description="email address or account ID of user",
        ),
    ],
)

financial_move_money = ToolDefinition(
    name="FinMoveMoney",
    description="Send money from one account to another under the same acount ID (e.g. checking to savings). "
    "Returns the status of the order and the new balances in each account. ",
    arguments=[
        ToolArgument(
            name="email_address_or_account_ID",
            type="string",
            description="email address or account ID of user (you will need both to find the account)",
        ),
        ToolArgument(
            name="accounttype",
            type="string",
            description="account type, such as checking or savings",
        ),
        ToolArgument(
            name="amount",
            type="string",
            description="amount to move in the order (e.g. checking or savings)",
        ),
        ToolArgument(
            name="destinationaccount",
            type="string",
            description="account to move the money to (e.g. checking or savings)",
        ),
        ToolArgument(
            name="userConfirmation",
            type="string",
            description="Indication of user's desire to move money",
        ),
    ],
)

financial_submit_loan_approval = ToolDefinition(
    name="FinCheckAccountSubmitLoanApproval",
    description="Submit a loan application. " "Returns the loan status. ",
    arguments=[
        ToolArgument(
            name="email_address_or_account_ID",
            type="string",
            description="email address or account ID of user",
        ),
        ToolArgument(
            name="amount",
            type="string",
            description="amount requested for the loan",
        ),
    ],
)
