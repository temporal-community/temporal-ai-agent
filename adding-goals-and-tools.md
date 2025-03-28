## Customizing the Agent
The agent is set up to allow for multiple goals and to switch back to choosing a new goal at the end of every successful goal. A goal is made up of a list of tools that the agent will guide the user through. 

It may be helpful to review the [architecture](./architecture.md) for a guide and definition of goals, tools, etc.

### Adding a New Goal Category
Goal Categories lets you pick which groups of goals to show. Set via an .env setting, GOAL_CATEGORIES.
1. Pick a unique one that has some business meaning
2. Use it in your .env file
3. Add to [.env.example](./.env.example)
4. Use it in your Goal definition, see below.

### Adding a Goal
1.  Open [/tools/goal_registry.py](tools/goal_registry.py) - this file contains descriptions of goals and the tools used to achieve them
2. Pick a name for your goal! (such as "goal_hr_schedule_pto")
3. Fill out the required elements:
-  `id`: needs to be the same as the name
- `agent_name`: user-facing name for the agent/chatbot
- `category_tag`: category for the goal
- `agent_friendly_description`: user-facing description of what the agent/chatbot does
- `tools`: the list of tools the goal will walk the user through. These will be defined in the [tools/tool_registry.py](tools/tool_registry.py) and should be defined in list form as tool_registry.[name of tool]
- Important! The last tool listed must be `list_agents_tool`. This allows the chatbot to guide the user back to choosing from the list of available goals once a goal is complete.<br />
Example:
```
tools=[
    tool_registry.current_pto_tool,
    tool_registry.future_pto_calc_tool,
    tool_registry.book_pto_tool,
    tool_registry.list_agents_tool,
]
```
- `description`: LLM-facing description of the goal that lists the tools by name and purpose.
- `starter-prompt`: LLM-facing first prompt given to begin the scenario. This field can contain instructions that are different from other goals, like "begin by providing the output of the first tool" rather than waiting on user confirmation. (See [goal_choose_agent_type](tools/goal_registry.py) for an example.)
- `example_conversation_history`: LLM-facing sample conversation/interaction regarding the goal. See the existing goals for how to structure this.
4. Add your new goal to the `goal_list` at the bottom using `goal_list.append(your_super_sweet_new_goal)`

### Adding Tools

#### Notes
Tools can be optional - you can indicate this in the tool listing of goal description (see above section re: goal registry) by adding something like, "This step is optional and can be skipped by moving to the next tool." Here is an example from an older iteration of the `goal_hr_schedule_pto` goal, when it was going to have an optional step to check for existing calendar conflicts:

```
description="Help the user gather args for these tools in order: "
    "1. CurrentPTO: Tell the user how much PTO they currently have "
    "2. FuturePTO: Tell the user how much PTO they will have as of the prospective date "
    "3. CalendarConflict: Tell the user what conflicts if any exist around the prospective date on a list of calendars. This step is optional and can be skipped by moving to the next tool. "
    "4. BookPTO: Book PTO "
```

#### Add to Tool Registry
1.  Open [/tools/tool_registry.py](tools/tool_registry.py) - this file contains mapping of tool names to tool definitions (so the AI understands how to use them)
2. Define the tool
- `name`: name of the tool - this is the name as defined in the goal description list of tools. The name should be (sort of) the same as the tool name given in the goal description. So, if the description lists "CurrentPTO" as a tool, the name here should be `current_pto_tool`.
- `description`: LLM-facing description of tool
- `arguments`: These are the _input_ arguments to the tool. Each input argument should be defined as a [ToolArgument](./models/tool_definitions.py). Tools don't have to have arguments but the arguments list has to be declared. If the tool you're creating doesn't have inputs, define arguments as `arguments=[]`

#### Create Each Tool
- The tools themselves are defined in their own files in `/tools` - you can add a subfolder to organize them, see the hr tools for an example.
- The file name and function name will be the same as each other and should also be the same as the name of the tool, without "tool" - so `current_pto_tool` would be `current_pto.py` with a function named `current_pto` within it.
- The function should have `args: dict` as the input and also return a `dict`
- The return dict should match the output format you specified in the goal's `example_conversation_history`
- tools are where the user input+model output becomes deterministic. Add validation here to make sure what the system is doing is valid and acceptable

#### Add to `tools/__init__.py` and the tool get_handler()
- In [tools/__init__.py](./tools/__init__.py), add an import statement for each new tool as well as an applicable return statement in `get_handler`. The tool name here should match the tool name as described in the goal's `description` field.
Example:
```
if tool_name == "CurrentPTO":
    return current_pto
```
