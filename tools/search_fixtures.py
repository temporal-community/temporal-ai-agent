import os
import requests
from datetime import datetime
from dotenv import load_dotenv

BASE_URL = 'https://api.football-data.org/v4'

def search_fixtures(args: dict) -> dict:
    load_dotenv(override=True)
    api_key = os.getenv("FOOTBALL_DATA_API_KEY", "YOUR_DEFAULT_KEY")

    team_name = args.get("team")
    month = args.get("month")
    headers = {'X-Auth-Token': api_key}
    team_name = team_name.lower()
    month = month.capitalize()

    try:
        month_number = datetime.strptime(month, "%B").month
    except ValueError:
        return {"error": "Invalid month provided."}

    # Fetch team ID
    teams_response = requests.get(f'{BASE_URL}/competitions/PL/teams', headers=headers)
    if teams_response.status_code != 200:
        return {"error": "Failed to fetch teams data."}

    teams_data = teams_response.json()
    team_id = None
    for team in teams_data['teams']:
        if team_name in team['name'].lower():
            team_id = team['id']
            break

    if not team_id:
        return {"error": "Team not found."}

    # Fetch fixtures
    match_date_from = f'2025-{month_number:02}-01'
    match_date_to = f'2025-{month_number:02}-31'
    print(f'{BASE_URL}/teams/{team_id}/matches?dateFrom={match_date_from}&dateTo={match_date_to}')
    fixtures_response = requests.get(f'{BASE_URL}/teams/{team_id}/matches?dateFrom={match_date_from}&dateTo={match_date_to}', headers=headers)
    if fixtures_response.status_code != 200:
        return {"error": "Failed to fetch fixtures data."}

    fixtures_data = fixtures_response.json()
    matching_fixtures = []

    for match in fixtures_data['matches']:
        print(match)
        match_date = datetime.strptime(match['utcDate'], "%Y-%m-%dT%H:%M:%SZ")
        if match['competition']['code'] == 'PL':
            matching_fixtures.append({
                "date": match_date.strftime("%Y-%m-%d"),
                "homeTeam": match['homeTeam']['name'],
                "awayTeam": match['awayTeam']['name'],
            })

    return {"fixtures": matching_fixtures}
