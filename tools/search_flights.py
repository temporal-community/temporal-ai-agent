def search_flights(args: dict) -> dict:
    """
    Example function for searching flights.
    Currently just prints/returns the passed args,
    but you can add real flight search logic later.
    """
    # date_depart = args.get("dateDepart")
    # date_return = args.get("dateReturn")
    origin = args.get("origin")
    destination = args.get("destination")

    flight_search_results = {
        "origin": f"{origin}",
        "destination": f"{destination}",
        "currency": "USD",
        "results": [
            {"flight_number": "CX101", "return_flight_number": "CX102", "price": 850.0},
            {"flight_number": "QF30", "return_flight_number": "QF29", "price": 920.0},
            {"flight_number": "MH129", "return_flight_number": "MH128", "price": 780.0},
        ],
    }

    return flight_search_results
