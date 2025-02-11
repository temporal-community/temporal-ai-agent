from models.tool_definitions import ToolDefinition, ToolArgument

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
    description="Search for trains between two stations. Returns a list of trains.",
    arguments=[
        ToolArgument(
            name="origin",
            type="string",
            description="The station to depart from",
        ),
        ToolArgument(
            name="destination",
            type="string",
            description="The station to arrive at",
        ),
        ToolArgument(
            name="outbound_time",
            type="ISO8601",
            description="The date and time to search for outbound trains",
        ),
        ToolArgument(
            name="return_time",
            type="ISO8601",
            description="The date and time to search for return trains",
        ),
    ],
)

book_train_tool = ToolDefinition(
    name="BookTrain",
    description="Books a train ticket. Returns a booking reference.",
    arguments=[
        ToolArgument(
            name="journey_id",
            type="string",
            description="The ID of the journey to book",
        ),
    ],
)

create_invoice_tool = ToolDefinition(
    name="CreateInvoice",
    description="Generate an invoice for the items described for the amount provided. Returns URL to invoice.",
    arguments=[
        ToolArgument(
            name="amount",
            type="float",
            description="The total cost to be invoiced",
        ),
        ToolArgument(
            name="tripDetails",
            type="string",
            description="A description of the item details to be invoiced",
        ),
    ],
)

search_fixtures_tool = ToolDefinition(
    name="SearchFixtures",
    description="Search for upcoming fixtures for a given team and month",
    arguments=[
        ToolArgument(
            name="team",
            type="string",
            description="The full name of the team to search for.",
        ),
        ToolArgument(
            name="month",
            type="string",
            description="The month to search for fixtures.",
        ),
    ],
)
