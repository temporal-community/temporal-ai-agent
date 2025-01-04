import os
import json
import http.client
from dotenv import load_dotenv
import urllib.parse


def search_airport(query: str) -> list:
    """
    Returns a list of matching airports/cities from sky-scrapper's searchAirport endpoint.
    """
    load_dotenv()
    api_key = os.getenv("RAPIDAPI_KEY", "YOUR_DEFAULT_KEY")
    api_host = os.getenv("RAPIDAPI_HOST", "sky-scrapper.p.rapidapi.com")

    conn = http.client.HTTPSConnection(api_host)
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": api_host,
    }

    # Sanitize the query to ensure it is URL-safe
    print(f"Searching for: {query}")
    encoded_query = urllib.parse.quote(query)
    path = f"/api/v1/flights/searchAirport?query={encoded_query}&locale=en-US"

    conn.request("GET", path, headers=headers)
    res = conn.getresponse()
    if res.status != 200:
        print(f"Error: API responded with status code {res.status}")
        print(f"Response: {res.read().decode('utf-8')}")
        return []

    data = res.read()
    conn.close()

    try:
        return json.loads(data).get("data", [])
    except json.JSONDecodeError:
        return []


def search_flights_realapi(args: dict) -> dict:
    """
    1) Looks up airport/city codes via search_airport.
    2) Finds the first matching skyId/entityId for both origin & destination.
    3) Calls the flight search endpoint with those codes.
    """
    date_depart = args.get("dateDepart")
    date_return = args.get("dateReturn")
    origin_query = args.get("origin")
    dest_query = args.get("destination")

    # Step 1: Resolve skyIds
    origin_candidates = search_airport(origin_query)
    destination_candidates = search_airport(dest_query)

    if not origin_candidates or not destination_candidates:
        return {"error": "No matches found for origin/destination"}

    origin_params = origin_candidates[0]["navigation"]["relevantFlightParams"]
    dest_params = destination_candidates[0]["navigation"]["relevantFlightParams"]

    origin_sky_id = origin_params["skyId"]  # e.g. "LOND"
    origin_entity_id = origin_params["entityId"]  # e.g. "27544008"
    dest_sky_id = dest_params["skyId"]  # e.g. "NYCA"
    dest_entity_id = dest_params["entityId"]  # e.g. "27537542"

    # Step 2: Call flight search with resolved codes
    load_dotenv()
    api_key = os.getenv("RAPIDAPI_KEY", "YOUR_DEFAULT_KEY")
    api_host = os.getenv("RAPIDAPI_HOST", "sky-scrapper.p.rapidapi.com")

    conn = http.client.HTTPSConnection(api_host)
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": api_host,
    }

    path = (
        "/api/v2/flights/searchFlights?"
        f"originSkyId={origin_sky_id}"
        f"&destinationSkyId={dest_sky_id}"
        f"&originEntityId={origin_entity_id}"
        f"&destinationEntityId={dest_entity_id}"
        f"&date={date_depart}"
        f"&returnDate={date_return}"
        f"&cabinClass=economy&adults=1&sortBy=best&currency=USD"
        f"&market=en-US&countryCode=US"
    )

    conn.request("GET", path, headers=headers)
    res = conn.getresponse()
    data = res.read()
    conn.close()

    try:
        json_data = json.loads(data)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response"}

    itineraries = json_data.get("data", {}).get("itineraries", [])
    if not itineraries:
        return json_data  # Return raw response for debugging if itineraries are empty

    formatted_results = []
    seen_carriers = set()

    for itinerary in itineraries:
        legs = itinerary.get("legs", [])
        if len(legs) >= 2:
            # Extract outbound and return flight details
            outbound_leg = legs[0]
            return_leg = legs[1]

            # Get the first segment for flight details
            outbound_flight = outbound_leg.get("segments", [{}])[0]
            return_flight = return_leg.get("segments", [{}])[0]

            # Extract flight details
            outbound_carrier = outbound_flight.get("operatingCarrier", {}).get(
                "name", "N/A"
            )
            outbound_carrier_code = outbound_flight.get("operatingCarrier", {}).get(
                "alternateId", ""
            )
            outbound_flight_number = outbound_flight.get("flightNumber", "N/A")
            outbound_flight_code = (
                f"{outbound_carrier_code}{outbound_flight_number}"
                if outbound_carrier_code
                else outbound_flight_number
            )

            return_carrier = return_flight.get("operatingCarrier", {}).get(
                "name", "N/A"
            )
            return_carrier_code = return_flight.get("operatingCarrier", {}).get(
                "alternateId", ""
            )
            return_flight_number = return_flight.get("flightNumber", "N/A")
            return_flight_code = (
                f"{return_carrier_code}{return_flight_number}"
                if return_carrier_code
                else return_flight_number
            )

            # Check if carrier is unique
            if outbound_carrier not in seen_carriers:
                seen_carriers.add(outbound_carrier)  # Add to seen carriers
                formatted_results.append(
                    {
                        "outbound_flight_code": outbound_flight_code,
                        "operating_carrier": outbound_carrier,
                        "return_flight_code": return_flight_code,
                        "return_operating_carrier": return_carrier,
                        "price": itinerary.get("price", {}).get("raw", 0.0),
                    }
                )

            # Stop after finding 3 unique carriers
            if len(formatted_results) >= 3:
                break

    return {
        "origin": origin_query,
        "destination": dest_query,
        "currency": "USD",
        "results": formatted_results,
    }


def search_flights(args: dict) -> dict:
    """
    Returns example flight search results in the requested JSON format.
    """
    origin = args.get("origin")
    destination = args.get("destination")

    return {
        "currency": "USD",
        "destination": f"{destination}",
        "origin": f"{origin}",
        "results": [
            {
                "operating_carrier": "American Airlines",
                "outbound_flight_code": "AA203",
                "price": 1262.51,
                "return_flight_code": "AA202",
                "return_operating_carrier": "American Airlines",
            },
            {
                "operating_carrier": "Air New Zealand",
                "outbound_flight_code": "NZ488",
                "price": 1396.00,
                "return_flight_code": "NZ527",
                "return_operating_carrier": "Air New Zealand",
            },
        ],
    }
