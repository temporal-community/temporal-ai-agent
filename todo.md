# todo list
[ ] mergey stuffs <br />
- [x] make confirm work how you want when force_confirm is on and off <br />
    - [x] test with confirm on and off - single goal <br />
        - [x] confirmation off-> it's unclear it's asking for confirmation unless we set `self.confirm = False` in the workflow  - maybe we should take the args/confirm route? - test with confirm on box - test with book PTO<br />
    - [x] test with confirm on and off - multi goal <br />
- [x] documenting confirm <br />
- [x] document how to do debugging confirm force confirm with toolchain in setup and adding-goals-and-tools <br />
- [x] document how to do optional confirm at goal/tool level <br /> 
- [ ] goal change management tweaks <br />
    - [ ] maybe make the choose_Agent_goal tag not be system/not always included? <br />
    - [ ] try taking out list-agents as a tool because agent_prompt_generators may do it for you <br />
    - [ ] make goal selection not be a system tool but be an option in .env, see how that works, includes taking it out of the goal/toolset for all goals <br />
- [x] make the goal selection/capabilities work how you want <br />
- [x] make end-conversation work when force_confirm is on and off <br />


- [x] make tool selection work  when force_confirm is on and off <br />

- [x] updates to PTO and money movement setup docs re data file <br />
- [x] fixing NDE about changing force_confirm <br />
- [x] rename self.confirm to self.confirmed to be clearer
- [x] rename show_confirm to show_confirm_and_tool_args

- [x] remove print debugging and todo comments
[ ] expand [tests](./tests/agent_goal_workflow_test.py)<br />
[ ] try claude-3-7-sonnet-20250219, see [tool_activities.py](./activities/tool_activities.py) <br />
[x] make agent respond to name of goals and not just numbers <br />
[x] josh to do fintech scenarios <br />


[ ] fintech goals <br />
- Fraud Detection and Prevention - The AI monitors transactions across accounts, flagging suspicious activities (e.g., unusual spending patterns or login attempts) and autonomously freezing accounts or notifying customers and compliance teams.<br />
- Personalized Financial Advice - An AI agent analyzes a customer’s financial data (e.g., income, spending habits, savings, investments) and provides tailored advice, such as budgeting tips, investment options, or debt repayment strategies.<br />
- Portfolio Management and Rebalancing - The AI monitors a customer’s investment portfolio, rebalancing it automatically based on market trends, risk tolerance, and financial goals (e.g., shifting assets between stocks, bonds, or crypto).<br />

[ ] new loan/fraud check/update with start <br />


[ ] ask the ai agent how it did at the end of the conversation, was it efficient? successful? insert a search attribute to document that before return <br />
- Insight into the agent’s performance <br />
[ ] non-retry the api key error - "Invalid API Key provided: sk_test_**J..." and "AuthenticationError" <br />
[ ] add visual feedback when workflow starting <br />
[ ] enable user to list agents at any time - like end conversation - probably with a next step<br />
 - with changing "'Next should only be "pick-new-goal" if all tools have been run (use the system prompt to figure that out).'" in [prompt_generators](./prompts/agent_prompt_generators.py).