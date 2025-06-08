from typing import List

import tools.tool_registry as tool_registry
from models.tool_definitions import AgentGoal

# Turn on Silly Mode - this should be a description of the persona you'd like the bot to have and can be a single word or a phrase.
# Example if you want the bot to be a specific person, like Mario or Christopher Walken, or to describe a specific tone:
# SILLY_MODE="Christopher Walken"
# SILLY_MODE="belligerent"
#
# Example if you want it to take on a persona (include 'a'):
# SILLY_MODE="a pirate"
# Note - this only works with certain LLMs. Grok for sure will stay in character, while OpenAI will not.
SILLY_MODE = "off"
if SILLY_MODE is not None and SILLY_MODE != "off":
    silly_prompt = "You are " + SILLY_MODE + ", stay in character at all times. "
    print("Silly mode is on: " + SILLY_MODE)
else:
    silly_prompt = ""

starter_prompt_generic = (
    silly_prompt
    + "Welcome me, give me a description of what you can do, then ask me for the details you need to do your job."
)

goal_choose_agent_type = AgentGoal(
    id="goal_choose_agent_type",
    category_tag="agent_selection",
    agent_name="Choose Agent",
    agent_friendly_description="Choose the type of agent to assist you today. You can always interrupt an existing agent to pick a new one.",
    tools=[
        tool_registry.list_agents_tool,
        tool_registry.change_goal_tool,
    ],
    description="The user wants to choose which type of agent they will interact with. "
    "Help the user select an agent by gathering args for the Changegoal tool, in order: "
    "1. ListAgents: List agents available to interact with. Do not ask for user confirmation for this tool. "
    "2. ChangeGoal: Change goal of agent "
    "After these tools are complete, change your goal to the new goal as chosen by the user. ",
    starter_prompt=silly_prompt
    + "Welcome me, give me a description of what you can do, then ask me for the details you need to do your job. List all details of all agents as provided by the output of the first tool included in this goal. ",
    example_conversation_history="\n ".join(
        [
            "agent: Here are the currently available agents.",
            "tool_result: { agents: 'agent_name': 'Event Flight Finder', 'goal_id': 'goal_event_flight_invoice', 'agent_description': 'Helps users find interesting events and arrange travel to them',"
            "'agent_name': 'Schedule PTO', 'goal_id': 'goal_hr_schedule_pto', 'agent_description': 'Schedule PTO based on your available PTO.' }",
            "agent: The available agents are: Event Flight Finder and Schedule PTO. \n Which agent would you like to work with? ",
            "user: I'd like to find an event and book flights using the Event Flight Finder",
            "user_confirmed_tool_run: <user clicks confirm on ChangeGoal tool>",
            "tool_result: { 'new_goal': 'goal_event_flight_invoice' }",
        ]
    ),
)

# Easter egg - if silly mode = a pirate, include goal_pirate_treasure as a "system" goal so it always shows up.
# Can also turn make this goal available by setting the GOAL_CATEGORIES in the env file to include 'pirate', but if SILLY_MODE
#   is not 'a pirate', the interaction as a whole will be less pirate-y.
pirate_category_tag = "pirate"
if SILLY_MODE == "a pirate":
    pirate_category_tag = "system"
goal_pirate_treasure = AgentGoal(
    id="goal_pirate_treasure",
    category_tag=pirate_category_tag,
    agent_name="Arrr, Find Me Treasure!",
    agent_friendly_description="Sail the high seas and find me pirate treasure, ye land lubber!",
    tools=[
        tool_registry.give_hint_tool,
        tool_registry.guess_location_tool,
    ],
    description="The user wants to find a pirate treasure. "
    "Help the user gather args for these tools, in a loop, until treasure_found is True or the user requests to be done: "
    "1. GiveHint: If the user wants a hint regarding the location of the treasure, give them a hint. If they do not want a hint, this tool is optional."
    "2. GuessLocation: The user guesses where the treasure is, by giving an address. ",
    starter_prompt=starter_prompt_generic,
    example_conversation_history="\n ".join(
        [
            "user: I'd like to try to find the treasure",
            "agent: Sure! Do you want a hint?",
            "user: yes",
            "agent: Here is hint number 1!",
            "user_confirmed_tool_run: <user clicks confirm on GiveHint tool>",
            "tool_result: { 'hint_number': 1, 'hint': 'The treasure is in the state of Arizona.' }",
            "agent: The treasure is in the state of Arizona. Would you like to guess the address of the treasure? ",
            "user: Yes, address is 123 Main St Phoenix, AZ",
            "agent: Let's see if you found the treasure...",
            "user_confirmed_tool_run: <user clicks confirm on GuessLocation tool>"
            "tool_result: {'treasure_found':False}",
            "agent: Nope, that's not the right location! Do you want another hint?",
            "user: yes",
            "agent: Here is hint number 2.",
            "user_confirmed_tool_run: <user clicks confirm on GiveHint tool>",
            "tool_result: { 'hint_number': 2, 'hint': 'The treasure is in the city of Tucson, AZ.' }",
            "agent: The treasure is in the city of Tucson, AZ. Would you like to guess the address of the treasure? ",
            "user: Yes, address is 456 Main St Tucson, AZ",
            "agent: Let's see if you found the treasure...",
            "user_confirmed_tool_run: <user clicks confirm on GuessLocation tool>",
            "tool_result: {'treasure_found':True}",
            "agent: Congratulations, Land Lubber, you've found the pirate treasure!",
        ]
    ),
)

agent_selection_goals: List[AgentGoal] = [
    goal_choose_agent_type,
    goal_pirate_treasure,
]