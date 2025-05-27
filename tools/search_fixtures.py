import os
import requests
import random
from datetime import datetime, timedelta, date
from dotenv import load_dotenv

PREMIER_LEAGUE_CLUBS_DATA = [
    {"name": "Arsenal FC", "stadium": "Emirates Stadium"},
    {"name": "Aston Villa FC", "stadium": "Villa Park"},
    {"name": "AFC Bournemouth", "stadium": "Vitality Stadium"},
    {"name": "Brentford FC", "stadium": "Gtech Community Stadium"},
    {"name": "Brighton & Hove Albion FC", "stadium": "American Express Stadium"},
    {"name": "Chelsea FC", "stadium": "Stamford Bridge"},
    {"name": "Crystal Palace FC", "stadium": "Selhurst Park"},
    {"name": "Everton FC", "stadium": "Goodison Park"},
    {"name": "Fulham FC", "stadium": "Craven Cottage"},
    {"name": "Ipswich Town FC", "stadium": "Portman Road"},
    {"name": "Leicester City FC", "stadium": "King Power Stadium"},
    {"name": "Liverpool FC", "stadium": "Anfield"},
    {"name": "Manchester City FC", "stadium": "Etihad Stadium"},
    {"name": "Manchester United FC", "stadium": "Old Trafford"},
    {"name": "Newcastle United FC", "stadium": "St James' Park"},
    {"name": "Nottingham Forest FC", "stadium": "City Ground"},
    {"name": "Southampton FC", "stadium": "St Mary's Stadium"},
    {"name": "Tottenham Hotspur FC", "stadium": "Tottenham Hotspur Stadium"},
    {"name": "West Ham United FC", "stadium": "London Stadium"},
    {"name": "Wolverhampton Wanderers FC", "stadium": "Molineux Stadium"},
]


def get_future_matches(
    team_name: str,
    all_clubs_data: list,
    num_matches: int = 12,
    date_from: date = None,
    date_to: date = None,
) -> list:
    """Generate a set of future Premier League matches for ``team_name``.

    This is a purely mocked schedule. It returns up to ``num_matches``
    fixtures, respecting the ``date_from`` and ``date_to`` constraints.
    Matches are typically on Saturdays or Sundays.
    """
    matches = []

    team_details = next((c for c in all_clubs_data if c["name"] == team_name), None)
    if not team_details:
        return []

    opponents_pool = [c for c in all_clubs_data if c["name"] != team_name]
    if not opponents_pool:
        return []

    # Determine the maximum number of matches we can generate based on opponents
    # and the requested num_matches
    num_actual_matches_to_generate = min(num_matches, len(opponents_pool))
    if num_actual_matches_to_generate == 0:
        return []

    # Shuffle opponents once and pick them sequentially
    random.shuffle(opponents_pool)  # Shuffle in place

    # Determine the initial Saturday for match week consideration
    today_date = date.today()
    # Default to next Saturday
    current_match_week_saturday = today_date + timedelta(
        days=(5 - today_date.weekday() + 7) % 7
    )

    # If today is Saturday and it's late evening, or if today is Sunday,
    # advance to the following Saturday.
    now_time = datetime.now().time()
    if (
        today_date.weekday() == 5
        and now_time > datetime.strptime("20:00", "%H:%M").time()
    ) or (today_date.weekday() == 6):
        current_match_week_saturday += timedelta(days=7)

    # If date_from is specified, ensure our starting Saturday is not before it.
    if date_from:
        if current_match_week_saturday < date_from:
            current_match_week_saturday = date_from
        # Align current_match_week_saturday to be a Saturday on or after the potentially adjusted date
        current_match_week_saturday += timedelta(
            days=(5 - current_match_week_saturday.weekday() + 7) % 7
        )

    opponent_idx = 0
    while len(matches) < num_actual_matches_to_generate and opponent_idx < len(
        opponents_pool
    ):
        # If the current week's Saturday is already past date_to, stop.
        if date_to and current_match_week_saturday > date_to:
            break

        opponent_details = opponents_pool[opponent_idx]
        is_saturday_game = random.choice([True, True, False])
        actual_match_date = None
        kick_off_time = ""

        if is_saturday_game:
            actual_match_date = current_match_week_saturday
            kick_off_time = random.choice(["12:30", "15:00", "17:30"])
        else:  # Sunday game
            actual_match_date = current_match_week_saturday + timedelta(days=1)
            kick_off_time = random.choice(["14:00", "16:30"])

        # Check if this specific match date is within the date_to constraint
        if date_to and actual_match_date > date_to:
            # If this game is too late, try the next week if possible.
            # (This mainly affects Sunday games if Saturday was the last valid day)
            current_match_week_saturday += timedelta(days=7)
            continue  # Skip adding this match, try next week.

        match_datetime_gmt = (
            f"{actual_match_date.strftime('%Y-%m-%d')} {kick_off_time} GMT"
        )
        is_home_match = random.choice([True, False])

        if is_home_match:
            team1_name = team_details["name"]
            team2_name = opponent_details["name"]
            stadium_name = team_details["stadium"]
        else:
            team1_name = opponent_details["name"]
            team2_name = team_details["name"]
            stadium_name = opponent_details["stadium"]

        matches.append(
            {
                "team1": team1_name,
                "team2": team2_name,
                "stadium": stadium_name,
                "datetime_gmt": match_datetime_gmt,
            }
        )
        opponent_idx += 1
        current_match_week_saturday += timedelta(
            days=7
        )  # Advance to next week's Saturday

    return matches


BASE_URL = "https://api.football-data.org/v4"


def search_fixtures(args: dict) -> dict:
    load_dotenv(override=True)
    api_key = os.getenv("FOOTBALL_DATA_API_KEY")

    team_name = args.get("team")
    date_from_str = args.get("date_from")
    date_to_str = args.get("date_to")

    if not team_name:
        return {"error": "Team name is required."}

    parsed_date_from = None
    if date_from_str:
        try:
            parsed_date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date()
        except ValueError:
            return {
                "error": f"Invalid date_from: '{date_from_str}'. Expected format YYYY-MM-DD."
            }

    parsed_date_to = None
    if date_to_str:
        try:
            parsed_date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date()
        except ValueError:
            return {
                "error": f"Invalid date_to: '{date_to_str}'. Expected format YYYY-MM-DD."
            }

    if parsed_date_from and parsed_date_to and parsed_date_from > parsed_date_to:
        return {"error": "date_from cannot be after date_to."}

    # If no API key, fall back to mocked data
    if not api_key:
        # Use the parsed date objects (which can be None)
        fixtures = get_future_matches(
            team_name,
            PREMIER_LEAGUE_CLUBS_DATA,
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            # num_matches can be passed explicitly if needed, otherwise defaults to 12
        )
        if not fixtures:
            # Check if the team name itself was invalid, as get_future_matches returns [] for that too
            team_details_check = next(
                (c for c in PREMIER_LEAGUE_CLUBS_DATA if c["name"] == team_name), None
            )
            if not team_details_check:
                return {"error": f"Team '{team_name}' not found in mocked data."}
            # If team is valid, an empty fixtures list means no matches fit the criteria (e.g., date range)
        return {"fixtures": fixtures}

    # API Key is present, proceed with API logic
    # The API requires both date_from and date_to
    if not parsed_date_from or not parsed_date_to:
        return {
            "error": "Both date_from and date_to (YYYY-MM-DD) are required for API search."
        }

    headers = {"X-Auth-Token": api_key}
    # For API calls, team name matching might be case-insensitive or require specific handling
    # The existing logic uses team_name.lower() for the API search path later.

    # Fetch team ID
    teams_response = requests.get(f"{BASE_URL}/competitions/PL/teams", headers=headers)
    if teams_response.status_code != 200:
        return {
            "error": f"Failed to fetch teams data from API (status {teams_response.status_code})."
        }

    teams_data = teams_response.json()
    team_id = None
    # Using lower() for comparison, assuming API team names might have varied casing
    # or the input team_name might not be exact.
    # The `ToolDefinition` lists exact names, so direct match might also be an option.
    for team_api_data in teams_data.get("teams", []):
        if team_name.lower() in team_api_data.get("name", "").lower():
            team_id = team_api_data["id"]
            break

    if not team_id:
        return {"error": f"Team '{team_name}' not found via API."}

    date_from_formatted = parsed_date_from.strftime("%Y-%m-%d")
    date_to_formatted = parsed_date_to.strftime("%Y-%m-%d")
    fixtures_url = f"{BASE_URL}/teams/{team_id}/matches?dateFrom={date_from_formatted}&dateTo={date_to_formatted}"
    # print(fixtures_url) # Keep for debugging if necessary

    fixtures_response = requests.get(fixtures_url, headers=headers)
    if fixtures_response.status_code != 200:
        return {
            "error": f"Failed to fetch fixtures data from API (status {fixtures_response.status_code})."
        }

    fixtures_data = fixtures_response.json()
    matching_fixtures = []

    for match in fixtures_data.get("matches", []):
        # Ensure match datetime parsing is robust
        try:
            match_datetime_utc = datetime.strptime(
                match["utcDate"], "%Y-%m-%dT%H:%M:%SZ"
            )
        except (ValueError, TypeError):
            # Skip malformed match entries or log an error
            continue

        if match.get("competition", {}).get("code") == "PL":
            matching_fixtures.append(
                {
                    "date": match_datetime_utc.strftime("%Y-%m-%d"),
                    "homeTeam": match.get("homeTeam", {}).get("name", "N/A"),
                    "awayTeam": match.get("awayTeam", {}).get("name", "N/A"),
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
        # Ensure date strings are not None before parsing
        if date_from_str is None or date_to_str is None:
            raise ValueError("Date strings cannot be None")
        date_from_obj = datetime.strptime(date_from_str, "%Y-%m-%d")
        date_to_obj = datetime.strptime(date_to_str, "%Y-%m-%d")
    except ValueError:
        return {
            "error": "Invalid date provided. Expected format YYYY-MM-DD for both date_from and date_to."
        }

    # Calculate 3 reasonable fixture dates within the given range
    date_range = (date_to_obj - date_from_obj).days
    if date_range < 0:  # date_from is after date_to
        return {"fixtures": []}  # No fixtures possible

    fixture_dates_timestamps = []
    if date_range < 21:
        # If range is less than 3 weeks, use evenly spaced fixtures if possible
        if date_range >= 2:  # Need at least some gap for 3 fixtures
            fixture_dates_timestamps = [
                date_from_obj
                + timedelta(days=max(0, date_range // 4)),  # Closer to start
                date_from_obj + timedelta(days=max(1, date_range // 2)),  # Middle
                date_to_obj - timedelta(days=max(0, date_range // 4)),  # Closer to end
            ]
        elif date_range == 1:  # Only two days
            fixture_dates_timestamps = [date_from_obj, date_to_obj]
        elif date_range == 0:  # Only one day
            fixture_dates_timestamps = [date_from_obj]
        else:  # date_range is negative, handled above, or 0 (single day)
            fixture_dates_timestamps = [date_from_obj] if date_range == 0 else []

    else:
        # Otherwise space them out by weeks, ensuring they are within the bounds
        d1 = date_from_obj + timedelta(days=7)
        d2 = date_from_obj + timedelta(days=14)
        d3 = date_to_obj - timedelta(days=7)  # Potential third game from the end

        fixture_dates_timestamps.append(d1)
        if d2 <= date_to_obj and d2 > d1:  # ensure d2 is valid and distinct
            fixture_dates_timestamps.append(d2)
        if (
            d3 >= date_from_obj and d3 > d2 and d3 <= date_to_obj
        ):  # ensure d3 is valid and distinct
            fixture_dates_timestamps.append(d3)
        elif (
            d3 < date_from_obj and len(fixture_dates_timestamps) < 3
        ):  # if d3 is too early, try using date_to_obj itself if distinct
            if date_to_obj not in fixture_dates_timestamps:
                fixture_dates_timestamps.append(date_to_obj)

    # Ensure unique dates and sort, then take up to 3.
    fixture_dates_timestamps = sorted(
        list(
            set(
                f_date
                for f_date in fixture_dates_timestamps
                if date_from_obj <= f_date <= date_to_obj
            )
        )
    )
    fixture_dates_final = fixture_dates_timestamps[:3]

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
        "Generic Opponent A",
        "Generic Opponent B",
        "Generic Opponent C",  # Fallbacks
    ]

    available_opponents = [
        team for team in all_opponents if team.lower() != team_name.lower()
    ]

    # Ensure we have enough opponents for the number of fixtures we'll generate
    if len(available_opponents) < len(fixture_dates_final):
        needed = len(fixture_dates_final) - len(available_opponents)
        for i in range(needed):
            available_opponents.append(f"Placeholder Opponent {i+1}")

    opponents = available_opponents[: len(fixture_dates_final)]

    fixtures = []
    for i, fixture_date_obj in enumerate(fixture_dates_final):
        if i >= len(opponents):  # Should not happen with the logic above
            break
        date_str = fixture_date_obj.strftime("%Y-%m-%d")
        if i % 2 == 0:  # Home game
            fixtures.append(
                {"date": date_str, "homeTeam": team_name, "awayTeam": opponents[i]}
            )
        else:  # Away game
            fixtures.append(
                {"date": date_str, "homeTeam": opponents[i], "awayTeam": team_name}
            )

    return {"fixtures": fixtures}
