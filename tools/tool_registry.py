from models.tool_definitions import ToolDefinition, ToolArgument

#This also doesn't help...
transfer_control_tool = ToolDefinition(
    name="TransferControl",
    description="Do one extra input from user to apply the new goal to the workflow (Hacky, hopefully temp). ",
    arguments=[        
        ToolArgument(
            name="userConfirmation",
            type="string",
            description="dummy variable to make thing work",
        ),
    ],
)


choose_agent_tool = ToolDefinition(
    name="ChooseAgent",
    description="List available agents to interact with, pulled from goal_registry. ",
    arguments=[        
        ToolArgument(
            name="userConfirmation",
            type="string",
            description="dummy variable to make thing work",
        ),
    ],
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

search_flights_tool = ToolDefinition(
    name="SearchFlights",
    description="Search for return flights from an origin to a destination within a date range (dateDepart, dateReturn).",
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
