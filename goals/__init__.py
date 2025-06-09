import os
from typing import List

import tools.tool_registry as tool_registry
from goals.agent_selection import agent_selection_goals
from goals.ecommerce import ecommerce_goals
from goals.finance import finance_goals
from goals.food import food_goals
from goals.hr import hr_goals
from goals.stripe_mcp import mcp_goals
from goals.travel import travel_goals
from models.tool_definitions import AgentGoal

goal_list: List[AgentGoal] = []
goal_list.extend(agent_selection_goals)
goal_list.extend(travel_goals)
goal_list.extend(hr_goals)
goal_list.extend(finance_goals)
goal_list.extend(ecommerce_goals)
goal_list.extend(mcp_goals)
goal_list.extend(food_goals)

# for multi-goal, just set list agents as the last tool
first_goal_value = os.getenv("AGENT_GOAL")
if first_goal_value is None:
    multi_goal_mode = False  # default to single agent mode if unset
elif (
    first_goal_value is not None
    and first_goal_value.lower() == "goal_choose_agent_type"
):
    multi_goal_mode = True
else:
    multi_goal_mode = False

if multi_goal_mode:
    for goal in goal_list:
        list_agents_found: bool = False
        for tool in goal.tools:
            if tool.name == "ListAgents":
                list_agents_found = True
                continue
        if list_agents_found is False:
            goal.tools.append(tool_registry.list_agents_tool)
            continue
