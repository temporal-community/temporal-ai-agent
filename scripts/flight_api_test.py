from tools.search_flights import search_flights
import json

if __name__ == "__main__":
    # Suppose user typed "new" for New York, "lon" for London
    flights = search_flights("London", "JFK", "2025-01-15", "2025-01-23")
    print(json.dumps(flights, indent=2))
