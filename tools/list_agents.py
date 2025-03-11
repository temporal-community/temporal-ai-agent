import tools.goal_registry as goals

def list_agents(args: dict) -> dict:

    agents = []
    if goals.goal_list is not None:
        for goal in goals.goal_list:
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
