# can this just call the API endpoint to set the goal, if that changes to allow a param?
# --- OR ---
# end this workflow and start a new one with the new goal
import shared.config

def change_goal(args: dict) -> dict:

    new_goal = args.get("goalID")
    shared.config.AGENT_GOAL = new_goal

    return {
        "new_goal": shared.config.AGENT_GOAL,
    }