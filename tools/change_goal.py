# can this just call the API endpoint to set the goal, if that changes to allow a param? 
#   if this functions, it could work to both send a signal and also circumvent the UI -> API thing. Maybe?

# --- OR ---

# end this workflow and start a new one with the new goal

# --- OR ---

# send a signal to the workflow from here?
import shared.config

def change_goal(args: dict) -> dict:

    new_goal = args.get("goalID")
    shared.config.AGENT_GOAL = new_goal

    return {
        "new_goal": shared.config.AGENT_GOAL,
    }