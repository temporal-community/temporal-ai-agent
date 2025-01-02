from models.tool_definitions import ToolDefinition, ToolArgument

find_events_tool = ToolDefinition(
    name="FindEvents",
    description="Find upcoming events given a location or region (e.g., 'Oceania') and a date or month",
    arguments=[
        ToolArgument(
            name="continent",
            type="string",
            description="Which continent or region to search for events",
        ),
        ToolArgument(
            name="month",
            type="string",
            description="The month or approximate date range to find events",
        ),
    ],
)

# 2) Define the SearchFlights tool
search_flights_tool = ToolDefinition(
    name="SearchFlights",
    description="Search for return flights from an origin to a destination within a date range (dateDepart, dateReturn)",
    arguments=[
        ToolArgument(
            name="origin",
            type="string",
            description="Airport or city (infer airport code from city)",
        ),
        ToolArgument(
            name="destination",
            type="string",
            description="Airport or city code for arrival (infer airport code from city)",
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

# 3) Define the CreateInvoice tool
create_invoice_tool = ToolDefinition(
    name="CreateInvoice",
    description="Generate an invoice with flight information or other items to purchase",
    arguments=[
        ToolArgument(
            name="amount",
            type="float",
            description="The total cost to be invoiced",
        ),
        ToolArgument(
            name="flightDetails",
            type="string",
            description="A summary of the flights, e.g., flight numbers, price breakdown",
        ),
    ],
)

all_tools = [find_events_tool, search_flights_tool, create_invoice_tool]
