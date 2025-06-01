def change_goal(args: dict) -> dict:
    new_goal = args.get("goalID")
    if new_goal is None:
        new_goal = "goal_choose_agent_type"

    return {
        "new_goal": new_goal,
    }
