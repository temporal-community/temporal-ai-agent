# Customizing the Agent
The agent is set up to have multiple agents, each with their own goal. It supports switching back to choosing a new goal at the end of every successful goal (or even mid-goal). 

A goal can use two types of tools:
- **Native Tools**: Custom tools implemented directly in the codebase (in `/tools/`)
- **MCP Tools**: External tools accessed via Model Context Protocol (MCP) servers

It may be helpful to review the [architecture](./architecture.md) for a guide and definition of goals, tools, etc.

## Adding a New Goal Category
Goal Categories lets you pick which groups of goals to show. Set via an .env setting, `GOAL_CATEGORIES`. 
Even if you don't intend to use the goal in a multi-goal scenario, goal categories are useful for others.
1. Pick a unique one that has some business meaning
2. Use it in your [.env](./.env) file
3. Add to [.env.example](./.env.example)
4. Use it in your Goal definition, see below.

## Adding a Goal
1. Create a new Python file in the `/goals/` directory (e.g., `goals/my_category.py`) - these files contain descriptions of goals and the tools used to achieve them
2. Pick a name for your goal! (such as "goal_hr_schedule_pto")
3. Fill out the required elements:
-  `id`: needs to be the same as the name
- `agent_name`: user-facing name for the agent/chatbot
- `category_tag`: category for the goal
- `agent_friendly_description`: user-facing description of what the agent/chatbot does
- `tools`: the list of **native tools** the goal uses. These are defined in [tools/tool_registry.py](tools/tool_registry.py) as `tool_registry.[name_of_tool]`

Example:
```python
tools=[
    tool_registry.current_pto_tool,
    tool_registry.future_pto_calc_tool,
    tool_registry.book_pto_tool,
]
```
- `mcp_server_definition`: (Optional) MCP server configuration for external tools. Can use predefined configurations from `shared/mcp_config.py` or define custom ones. See [MCP Tools section](#adding-mcp-tools) below.
- `description`: LLM-facing description of the goal that lists all tools (native and MCP) by name and purpose.
- `starter_prompt`: LLM-facing first prompt given to begin the scenario. This field can contain instructions that are different from other goals, like "begin by providing the output of the first tool" rather than waiting on user confirmation. (See [goal_choose_agent_type](tools/goal_registry.py) for an example.)
- `example_conversation_history`: LLM-facing sample conversation/interaction regarding the goal. See the existing goals for how to structure this.
4. Add your new goal to a list variable (e.g., `my_category_goals: List[AgentGoal] = [your_super_sweet_new_goal]`)
5. Import and extend the goal list in `goals/__init__.py` by adding:
   - Import: `from goals.my_category import my_category_goals`
   - Extend: `goal_list.extend(my_category_goals)`

## Adding Native Tools

Native tools are custom implementations that run directly in your codebase. Use these for business logic specific to your application.

### Note on Optional Tools
Tools can be optional - you can indicate this in the tool listing of goal description (see above section re: goal registry) by adding something like, "This step is optional and can be skipped by moving to the next tool." Here is an example from an older iteration of the `goal_hr_schedule_pto` goal, when it was going to have an optional step to check for existing calendar conflicts:

```
description="Help the user gather args for these tools in order: "
    "1. CurrentPTO: Tell the user how much PTO they currently have "
    "2. FuturePTO: Tell the user how much PTO they will have as of the prospective date "
    "3. CalendarConflict: Tell the user what conflicts if any exist around the prospective date on a list of calendars. This step is optional and can be skipped by moving to the next tool. "
    "4. BookPTO: Book PTO "
```

Tools should generally return meaningful information and be generally ‘failsafe’ in returning a useful result based on input.
(If you're doing a local data approach like those in [.tools/data/](./tools/data/)) it's good to document how they can be setup to get a good result in tool specific [setup](./SETUP.md).

### Add to Tool Registry
1.  Open [/tools/tool_registry.py](tools/tool_registry.py) - this file contains mapping of tool names to tool definitions (so the AI understands how to use them)
2. Define the tool
- `name`: name of the tool - this is the name as defined in the goal description list of tools. The name should be (sort of) the same as the tool name given in the goal description. So, if the description lists "CurrentPTO" as a tool, the name here should be `current_pto_tool`.
- `description`: LLM-facing description of tool
- `arguments`: These are the _input_ arguments to the tool. Each input argument should be defined as a [ToolArgument](./models/tool_definitions.py). Tools don't have to have arguments but the arguments list has to be declared. If the tool you're creating doesn't have inputs, define arguments as `arguments=[]`

### Create Each Native Tool Implementation
- The tools themselves are defined in their own files in `/tools` - you can add a subfolder to organize them, see the hr tools for an example.
- The file name and function name will be the same as each other and should also be the same as the name of the tool, without "tool" - so `current_pto_tool` would be `current_pto.py` with a function named `current_pto` within it.
- The function should have `args: dict` as the input and also return a `dict`
- The return dict should match the output format you specified in the goal's `example_conversation_history`
- tools are where the user input+model output becomes deterministic. Add validation here to make sure what the system is doing is valid and acceptable

### Add to `tools/__init__.py` and the tool get_handler()
- In [tools/__init__.py](./tools/__init__.py), add an import statement for each new native tool as well as an applicable return statement in `get_handler`. The tool name here should match the tool name as described in the goal's `description` field.
Example:
```python
if tool_name == "CurrentPTO":
    return current_pto
```

### Update workflow_helpers.py
- Add your new native tool to the static tools list in [workflows/workflow_helpers.py](workflows/workflow_helpers.py) so it's correctly identified as a native tool rather than an MCP tool.

## Adding MCP Tools

MCP (Model Context Protocol) tools are external tools provided by MCP servers. They're useful for integrating with third-party services like Stripe, databases, or APIs without implementing custom code.

### Configure MCP Server Definition
You can either use predefined MCP server configurations from `shared/mcp_config.py` or define custom ones. 

#### Using Predefined Configurations
```python
from shared.mcp_config import get_stripe_mcp_server_definition

# In your goal definition:
mcp_server_definition=get_stripe_mcp_server_definition(included_tools=["list_products", "create_customer"])
```

#### Custom MCP Server Definition
Add an `mcp_server_definition` to your goal:

```python
mcp_server_definition=MCPServerDefinition(
    name="stripe-mcp",
    command="npx",
    args=[
        "-y",
        "@stripe/mcp",
        "--tools=all",
        f"--api-key={os.getenv('STRIPE_API_KEY')}",
    ],
    env=None,
    included_tools=[
        "list_products",
        "list_prices", 
        "create_customer",
        "create_invoice",
        "create_payment_link",
    ],
)
```

### MCP Tool Configuration
- `name`: Identifier for the MCP server
- `command`: Command to start the MCP server (e.g., "npx", "python")
- `args`: Arguments to pass to the command
- `env`: Environment variables for the server (optional)
- `included_tools`: List of specific tools to use from the server (optional - if omitted, all tools are included)

### How MCP Tools Work
- MCP tools are automatically loaded when the workflow starts
- They're dynamically converted to `ToolDefinition` objects
- The system automatically routes MCP tool calls to the appropriate MCP server
- No additional code implementation needed - just configuration

## Tool Confirmation
There are three ways to manage confirmation of tool runs:
1. Arguments confirmation box - confirm tool arguments and execution with a button click
   -  Can be disabled by env setting: `SHOW_CONFIRM=FALSE`
2. Soft prompt confirmation via asking the model to prompt for confirmation: “Are you ready to be invoiced for the total cost of the train tickets?” in the [goal_registry](./tools/goal_registry.py).
3. Hard confirmation requirement as a tool argument. See for example the PTO Scheduling Tool:
```Python
        ToolArgument(
            name="userConfirmation",
            type="string",
            description="Indication of user's desire to book PTO",
        ),
```
If you really want to wait for user confirmation, record it on the workflow (as a Signal) and not rely on the LLM to probably get it, use option #3. 
I recommend exploring all three. For a demo, I would decide if you want the Arguments confirmation in the UI, and if not I'd generally go with option #2 but use #3 for tools that make business sense to confirm, e.g. those tools that take action/write data.

## Add a Goal & Tools Checklist

### For All Goals:
- [ ] Create goal file in `/goals/` directory (e.g., `goals/my_category.py`)
- [ ] Add goal to the category's goal list in the file
- [ ] Import and extend the goal list in `goals/__init__.py`
- [ ] If a new category, add Goal Category to [.env](./.env) and [.env.example](./.env.example)

### For Native Tools:
- [ ] Add native tools to [tool_registry.py](tools/tool_registry.py)
- [ ] Implement tool functions in `/tools/` directory
- [ ] Add tools to [tools/__init__.py](tools/__init__.py) in the `get_handler()` function
- [ ] Add tool names to static tools list in [workflows/workflow_helpers.py](workflows/workflow_helpers.py)

### For MCP Tools:
- [ ] Add `mcp_server_definition` to your goal configuration (use `shared/mcp_config.py` for common servers)
- [ ] Ensure MCP server is available and properly configured
- [ ] Set required environment variables (API keys, etc.)
- [ ] Test MCP server connectivity before running the agent
- [ ] If creating new MCP server configs, add them to `shared/mcp_config.py` for reuse

And that's it! Happy AI Agent building!
