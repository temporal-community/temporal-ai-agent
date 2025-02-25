import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

BASE_URL = "https://api.football-data.org/v4"


def search_fixtures(args: dict) -> dict:
    load_dotenv(override=True)
    api_key = os.getenv("FOOTBALL_DATA_API_KEY", "YOUR_DEFAULT_KEY")

    team_name = args.get("team")
    date_from_str = args.get("date_from")
    date_to_str = args.get("date_to")
    headers = {"X-Auth-Token": api_key}
    team_name = team_name.lower()

    try:
        date_from = datetime.strptime(date_from_str, "%Y-%m-%d")
        date_to = datetime.strptime(date_to_str, "%Y-%m-%d")
    except ValueError:
        return {
            "error": "Invalid date provided. Expected format YYYY-MM-DD for both date_from and date_to."
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

    date_from_formatted = date_from.strftime("%Y-%m-%d")
    date_to_formatted = date_to.strftime("%Y-%m-%d")
    fixtures_url = f"{BASE_URL}/teams/{team_id}/matches?dateFrom={date_from_formatted}&dateTo={date_to_formatted}"
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


def search_fixtures_example(args: dict) -> dict:
    """
    Example version of search_fixtures that returns hardcoded data without making API calls.
    The function respects the team name provided and generates fixture dates within the specified range.

    Args:
        args: Dictionary containing 'team', 'date_from', and 'date_to'

    Returns:
        Dictionary with 'fixtures' key containing a list of fixture objects
    """
    team_name = args.get("team", "Default Team FC")
    date_from_str = args.get("date_from")
    date_to_str = args.get("date_to")

    # Validate dates
    try:
        date_from = datetime.strptime(date_from_str, "%Y-%m-%d")
        date_to = datetime.strptime(date_to_str, "%Y-%m-%d")
    except ValueError:
        return {
            "error": "Invalid date provided. Expected format YYYY-MM-DD for both date_from and date_to."
        }

    # Calculate 3 reasonable fixture dates within the given range
    date_range = (date_to - date_from).days
    if date_range < 21:
        # If range is less than 3 weeks, use evenly spaced fixtures
        fixture_dates = [
            date_from + timedelta(days=max(1, date_range // 3)),
            date_from + timedelta(days=max(2, date_range * 2 // 3)),
            date_to - timedelta(days=min(2, date_range // 4)),
        ]
    else:
        # Otherwise space them out by weeks
        fixture_dates = [
            date_from + timedelta(days=7),
            date_from + timedelta(days=14),
            date_to - timedelta(days=7),
        ]

    # Ensure we only have 3 dates
    fixture_dates = fixture_dates[:3]

    # Expanded pool of opponent teams to avoid team playing against itself
    all_opponents = [
        "Manchester United FC",
        "Leicester City FC",
        "Manchester City FC",
        "Liverpool FC",
        "Chelsea FC",
        "Arsenal FC",
        "Tottenham Hotspur FC",
        "West Ham United FC",
        "Everton FC",
    ]

    # Select opponents that aren't the same as the requested team
    available_opponents = [
        team for team in all_opponents if team.lower() != team_name.lower()
    ]

    # Ensure we have at least 3 opponents
    if len(available_opponents) < 3:
        # Add generic opponents if needed
        additional_teams = [f"Opponent {i} FC" for i in range(1, 4)]
        available_opponents.extend(additional_teams)

    # Take only the first 3 opponents
    opponents = available_opponents[:3]

    # Generate fixtures - always exactly 3
    fixtures = []
    for i, fixture_date in enumerate(fixture_dates):
        date_str = fixture_date.strftime("%Y-%m-%d")

        # Alternate between home and away games
        if i % 2 == 0:
            fixtures.append(
                {"date": date_str, "homeTeam": opponents[i], "awayTeam": team_name}
            )
        else:
            fixtures.append(
                {"date": date_str, "homeTeam": team_name, "awayTeam": opponents[i]}
            )

    return {"fixtures": fixtures}
