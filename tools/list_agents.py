import os
import tools.goal_registry as goals

def list_agents(args: dict) -> dict:

    goal_categories_start = os.getenv("GOAL_CATEGORIES")
    if goal_categories_start is None:
        goal_categories = ["all"] # default to 'all' categories
    else:
        goal_categories_start.strip().lower() # handle extra spaces or non-lowercase
        goal_categories = goal_categories_start.split(",")

    # if multi-goal-mode, add agent_selection as a goal (defaults to True)
    if "agent_selection" not in goal_categories :
        first_goal_value = os.getenv("AGENT_GOAL")        
        if first_goal_value is None or first_goal_value.lower() == "goal_choose_agent_type":
            goal_categories.append("agent_selection")

    # always show goals labeled as "system," like the goal chooser
    if "system" not in goal_categories:
        goal_categories.append("system")

    agents = []
    if goals.goal_list is not None:
        for goal in goals.goal_list:
            # add to list if either
            #   - all
            #   - current goal's tag is in goal_categories
            if "all" in goal_categories or goal.category_tag in goal_categories:
                agents.append(
                    {
                        "agent_name": goal.agent_name,
                        "goal_id": goal.id,
                        "agent_description": goal.agent_friendly_description,
                    }
            )
    return {
        "agents": agents,
    }
