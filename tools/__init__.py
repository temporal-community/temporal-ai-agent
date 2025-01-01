from .search_flights import search_flights


def get_handler(tool_name: str):
    """
    Return a function reference for the given tool.
    You can add more tools here, e.g. "BookHotel", etc.
    """
    if tool_name == "SearchFlights":
        return search_flights

    # Or raise if not recognized
    raise ValueError(f"No handler found for tool '{tool_name}'")
