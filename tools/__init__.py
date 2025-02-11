from .search_fixtures import search_fixtures
from .search_flights import search_flights
from .search_trains import search_trains
from .search_trains import book_train
from .create_invoice import create_invoice


def get_handler(tool_name: str):
    if tool_name == "SearchFixtures":
        return search_fixtures
    if tool_name == "SearchFlights":
        return search_flights
    if tool_name == "SearchTrains":
        return search_trains
    if tool_name == "BookTrain":
        return book_train
    if tool_name == "CreateInvoice":
        return create_invoice

    raise ValueError(f"Unknown tool: {tool_name}")
