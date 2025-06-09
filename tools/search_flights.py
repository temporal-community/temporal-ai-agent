import http.client
import json
import os
import random
import urllib.parse

from dotenv import load_dotenv


def search_airport(query: str) -> list:
    """
    Returns a list of matching airports/cities from sky-scrapper's searchAirport endpoint.
    """
    load_dotenv(override=True)
    api_key = os.getenv("RAPIDAPI_KEY", "YOUR_DEFAULT_KEY")
    api_host = os.getenv("RAPIDAPI_HOST_FLIGHTS", "sky-scrapper.p.rapidapi.com")

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
        print("Error: Failed to decode JSON response")
        print(f"Response: {data.decode('utf-8')}")
        return []


def search_flights_real_api(
    args: dict,
) -> dict:  # rename to search_flights to use the real API
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
    load_dotenv(override=True)
    api_key = os.getenv("RAPIDAPI_KEY", "YOUR_DEFAULT_KEY")
    api_host = os.getenv("RAPIDAPI_HOST_FLIGHTS", "sky-scrapper.p.rapidapi.com")

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


def generate_smart_flights(origin: str, destination: str) -> list:
    """
    Generate realistic flight options with smart pricing based on origin and destination.
    """
    # Common airlines for different regions
    airlines_by_region = {
        "domestic_us": [
            {"name": "American Airlines", "code": "AA"},
            {"name": "United Airlines", "code": "UA"},
            {"name": "Delta Airlines", "code": "DL"},
            {"name": "Southwest Airlines", "code": "WN"},
        ],
        "us_international": [
            {"name": "American Airlines", "code": "AA"},
            {"name": "United Airlines", "code": "UA"},
            {"name": "Delta Airlines", "code": "DL"},
            {"name": "Virgin Atlantic", "code": "VS"},
        ],
        "australia_nz": [
            {"name": "Qantas", "code": "QF"},
            {"name": "Jetstar", "code": "JQ"},
            {"name": "Virgin Australia", "code": "VA"},
            {"name": "Air New Zealand", "code": "NZ"},
        ],
        "international": [
            {"name": "American Airlines", "code": "AA"},
            {"name": "United Airlines", "code": "UA"},
            {"name": "Delta Airlines", "code": "DL"},
            {"name": "Air New Zealand", "code": "NZ"},
            {"name": "Qantas", "code": "QF"},
            {"name": "Singapore Airlines", "code": "SQ"},
        ],
    }

    # Determine route type and base pricing
    origin_lower = origin.lower()
    dest_lower = destination.lower()

    # Australia/NZ cities
    anz_cities = [
        "sydney",
        "melbourne",
        "syd",
        "mel",
        "auckland",
        "akl",
        "wellington",
        "wlg",
        "brisbane",
        "bne",
        "perth",
        "per",
    ]
    # US cities
    us_cities = [
        "los angeles",
        "lax",
        "san francisco",
        "sfo",
        "new york",
        "nyc",
        "jfk",
        "chicago",
        "ord",
        "miami",
        "mia",
    ]

    is_origin_anz = any(city in origin_lower for city in anz_cities)
    is_dest_anz = any(city in dest_lower for city in anz_cities)
    is_origin_us = any(city in origin_lower for city in us_cities)
    is_dest_us = any(city in dest_lower for city in us_cities)

    # Determine airline pool and base price
    if (is_origin_us and is_dest_anz) or (is_origin_anz and is_dest_us):
        # Trans-Pacific routes
        airline_pool = airlines_by_region["international"]
        base_price = random.randint(1200, 1800)
    elif is_origin_anz and is_dest_anz:
        # Australia/NZ domestic
        airline_pool = airlines_by_region["australia_nz"]
        base_price = random.randint(300, 600)
    elif is_origin_us and is_dest_us:
        # US domestic
        airline_pool = airlines_by_region["domestic_us"]
        base_price = random.randint(200, 800)
    else:
        # General international
        airline_pool = airlines_by_region["international"]
        base_price = random.randint(800, 1500)

    # Generate 3-4 flight options
    num_flights = random.randint(3, 4)
    results = []
    used_airlines = set()

    for i in range(num_flights):
        # Pick unique airline
        available_airlines = [a for a in airline_pool if a["name"] not in used_airlines]
        if not available_airlines:
            available_airlines = airline_pool  # Reset if we run out

        airline = random.choice(available_airlines)
        used_airlines.add(airline["name"])

        # Generate flight numbers
        outbound_num = random.randint(100, 999)
        return_num = random.randint(100, 999)

        # Price variation (cheaper airlines get lower prices)
        price_multiplier = 1.0
        if "Southwest" in airline["name"] or "Jetstar" in airline["name"]:
            price_multiplier = 0.7
        elif "Virgin" in airline["name"]:
            price_multiplier = 0.85
        elif "Singapore" in airline["name"]:
            price_multiplier = 1.2

        # Add some random variation
        price_variation = random.uniform(0.9, 1.1)
        final_price = round(base_price * price_multiplier * price_variation, 2)

        results.append(
            {
                "operating_carrier": airline["name"],
                "outbound_flight_code": f"{airline['code']}{outbound_num}",
                "price": final_price,
                "return_flight_code": f"{airline['code']}{return_num}",
                "return_operating_carrier": airline["name"],
            }
        )

    # Sort by price
    results.sort(key=lambda x: x["price"])
    return results


def search_flights(args: dict) -> dict:
    """
    Search for flights. Uses real API if RAPIDAPI_KEY is available, otherwise generates smart mock data.
    """
    load_dotenv(override=True)
    api_key = os.getenv("RAPIDAPI_KEY")

    origin = args.get("origin")
    destination = args.get("destination")

    if not origin or not destination:
        return {"error": "Both origin and destination are required"}

    # If API key is available, use the real API
    if api_key and api_key != "YOUR_DEFAULT_KEY":
        return search_flights_real_api(args)

    # Otherwise, generate smart mock data
    results = generate_smart_flights(origin, destination)

    return {
        "currency": "USD",
        "destination": destination,
        "origin": origin,
        "results": results,
    }
