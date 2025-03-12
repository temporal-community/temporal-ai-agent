from .search_fixtures import search_fixtures
from .search_flights import search_flights
from .search_trains import search_trains
from .search_trains import book_trains
from .create_invoice import create_invoice
from .find_events import find_events
from .list_agents import list_agents
from .change_goal import change_goal
from .transfer_control import transfer_control


def get_handler(tool_name: str):
    if tool_name == "SearchFixtures":
        return search_fixtures
    if tool_name == "SearchFlights":
        return search_flights
    if tool_name == "SearchTrains":
        return search_trains
    if tool_name == "BookTrains":
        return book_trains
    if tool_name == "CreateInvoice":
        return create_invoice
    if tool_name == "FindEvents":
        return find_events
    if tool_name == "ListAgents":
        return list_agents
    if tool_name == "ChangeGoal":
        return change_goal
    if tool_name == "TransferControl":
        return transfer_control

    raise ValueError(f"Unknown tool: {tool_name}")
