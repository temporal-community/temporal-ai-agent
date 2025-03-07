from pathlib import Path
import json

def choose_agent(args: dict) -> dict:

   # file_path = Path(__file__).resolve().parent / "goal_regsitry.py"
    #if not file_path.exists():
      #  return {"error": "Data file not found."}

    agents = []
    agents.append(
        {
            "agent_name": "Event Flight Helper",
            "goal_id": "goal_event_flight_invoice",
            "agent_description": "Helps users find interesting events and arrange travel to them",
        }
    )
    agents.append(
        {
            "agent_name": "Soccer Train Thing Guy",
            "goal_id": "goal_match_train_invoice",
            "agent_description": "Something about soccer and trains and stuff",
        }
    )
    return {
        "agents": agents,
    }