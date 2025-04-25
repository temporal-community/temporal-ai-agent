from tools.search_flights import search_flights
import json

# Example usage
if __name__ == "__main__":
    search_args = {"city": "Sydney", "month": "July"}
    results = search_flights(search_args)
    print(json.dumps(results, indent=2))
