from .find_events import find_events
from .find_fixtures import find_fixtures
from .search_flights import search_flights
from .create_invoice import create_invoice


def get_handler(tool_name: str):
    if tool_name == "FindEvents":
        return find_events
    if tool_name == "FindFixtures":
        return find_fixtures
    if tool_name == "SearchFlights":
        return search_flights
    if tool_name == "CreateInvoice":
        return create_invoice

    raise ValueError(f"Unknown tool: {tool_name}")
