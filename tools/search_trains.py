import requests
import os
from dotenv import load_dotenv

BASE_URL = 'http://localhost:8080/'

def search_trains(args: dict) -> dict:
    load_dotenv(override=True)

    origin = args.get("origin")
    destination = args.get("destination")
    outbound_time = args.get("outbound_time")
    return_time = args.get("return_time")

    if not origin or not destination or not outbound_time or not return_time:
        return {"error": "Origin, destination, outbound_time and return_time are required."}

    search_url = f'{BASE_URL}/api/journeys'
    params = {
        'from': origin,
        'to': destination,
        'outbound_time': outbound_time,
        'return_time': return_time,
    }

    response = requests.get(search_url, params=params)
    if response.status_code != 200:
        print(response.content)
        return {"error": "Failed to fetch journey data."}

    journey_data = response.json()
    return journey_data

def book_train(args: dict) -> dict:
    load_dotenv(override=True)

    journey_id = args.get("journey_id")

    if not journey_id:
        return {"error": "Journey ID is required."}

    book_url = f'{BASE_URL}/api/book/{journey_id}'
    response = requests.post(book_url)
    if response.status_code != 200:
        return {"error": "Failed to book ticket."}

    booking_data = response.json()
    return booking_data

# Example usage
if __name__ == "__main__":
    search_args = {
        "origin": "London Gatwick",
        "destination": "Manchester",
        "outbound_time": "2025-03-15T14:00",
        "return_time": "2025-03-20T14:00"
    }
    search_results = search_trains(search_args)
    print(search_results)

    book_args = {
        "journey_id": "12345",
    }
    booking_results = book_train(book_args)
    print(booking_results)