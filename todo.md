# todo list
[ ] goal change management tweaks <br />
  - [x] maybe make the choose_Agent_goal tag not be system/not always included? <br />
  - [x] try taking out list-agents as a tool because agent_prompt_generators may do it for you <br />
  - [x] make goal selection not be a system tool but be an option in .env, see how that works, includes taking it out of the goal/toolset for all goals <br />
  - [x] test single-goal <br />
  - [x] test claude and grok<br />
  - [x] document in sample env and docs how to control <br />

[ ] expand [tests](./tests/agent_goal_workflow_test.py)<br />
[x] try claude-3-7-sonnet-20250219, see [tool_activities.py](./activities/tool_activities.py) <br />
[x] test Grok with changes

[ ] adding fintech goals <br />
- Fraud Detection and Prevention - The AI monitors transactions across accounts, flagging suspicious activities (e.g., unusual spending patterns or login attempts) and autonomously freezing accounts or notifying customers and compliance teams.<br />
- Personalized Financial Advice - An AI agent analyzes a customer’s financial data (e.g., income, spending habits, savings, investments) and provides tailored advice, such as budgeting tips, investment options, or debt repayment strategies.<br />
- Portfolio Management and Rebalancing - The AI monitors a customer’s investment portfolio, rebalancing it automatically based on market trends, risk tolerance, and financial goals (e.g., shifting assets between stocks, bonds, or crypto).<br />

[ ] new loan/fraud check/update with start <br />

[ ] for demo simulate failure  - add utilities/simulated failures from pipeline demo <br />

[ ] ask the ai agent how it did at the end of the conversation, was it efficient? successful? insert a search attribute to document that before return <br />
- Insight into the agent’s performance <br />
[ ] non-retry the api key error - "Invalid API Key provided: sk_test_**J..." and "AuthenticationError" <br />
[ ] add visual feedback when workflow starting <br />
[ ] enable user to list agents at any time - like end conversation - probably with a next step<br />
 - with changing "'Next should only be "pick-new-goal" if all tools have been run (use the system prompt to figure that out).'" in [prompt_generators](./prompts/agent_prompt_generators.py).