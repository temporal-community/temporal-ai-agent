from tools.search_events import find_events
import json

# Example usage
if __name__ == "__main__":
    search_args = {"city": "Sydney", "month": "July"}
    results = find_events(search_args)
    print(json.dumps(results, indent=2))
