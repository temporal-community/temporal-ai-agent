import os
import requests
from datetime import datetime
from dotenv import load_dotenv

BASE_URL = "https://api.football-data.org/v4"


def search_fixtures(args: dict) -> dict:
    load_dotenv(override=True)
    api_key = os.getenv("FOOTBALL_DATA_API_KEY", "YOUR_DEFAULT_KEY")

    team_name = args.get("team")
    start_date_str = args.get("start_date")
    end_date_str = args.get("end_date")
    headers = {"X-Auth-Token": api_key}
    team_name = team_name.lower()

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError:
        return {
            "error": "Invalid date provided. Expected format YYYY-MM-DD for both start_date and end_date."
        }

    # Fetch team ID
    teams_response = requests.get(f"{BASE_URL}/competitions/PL/teams", headers=headers)
    if teams_response.status_code != 200:
        return {"error": "Failed to fetch teams data."}

    teams_data = teams_response.json()
    team_id = None
    for team in teams_data["teams"]:
        if team_name in team["name"].lower():
            team_id = team["id"]
            break

    if not team_id:
        return {"error": "Team not found."}

    start_date_formatted = start_date.strftime("%Y-%m-%d")
    end_date_formatted = end_date.strftime("%Y-%m-%d")
    fixtures_url = f"{BASE_URL}/teams/{team_id}/matches?dateFrom={start_date_formatted}&dateTo={end_date_formatted}"
    print(fixtures_url)

    fixtures_response = requests.get(fixtures_url, headers=headers)
    if fixtures_response.status_code != 200:
        return {"error": "Failed to fetch fixtures data."}

    fixtures_data = fixtures_response.json()
    matching_fixtures = []

    for match in fixtures_data.get("matches", []):
        match_datetime = datetime.strptime(match["utcDate"], "%Y-%m-%dT%H:%M:%SZ")
        if match["competition"]["code"] == "PL":
            matching_fixtures.append(
                {
                    "date": match_datetime.strftime("%Y-%m-%d"),
                    "homeTeam": match["homeTeam"]["name"],
                    "awayTeam": match["awayTeam"]["name"],
                }
            )

    return {"fixtures": matching_fixtures}
