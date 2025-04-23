# todo list
[x] take steve's confirm box changes https://temporaltechnologies.slack.com/archives/D062SV8KEEM/p1745251279164319 <br />
[ ] consider adding goal categories to goal picker

[ ] adding fintech goals <br />
- Fraud Detection and Prevention - The AI monitors transactions across accounts, flagging suspicious activities (e.g., unusual spending patterns or login attempts) and autonomously freezing accounts or notifying customers and compliance teams.<br />
- Personalized Financial Advice - An AI agent analyzes a customer’s financial data (e.g., income, spending habits, savings, investments) and provides tailored advice, such as budgeting tips, investment options, or debt repayment strategies.<br />
- Portfolio Management and Rebalancing - The AI monitors a customer’s investment portfolio, rebalancing it automatically based on market trends, risk tolerance, and financial goals (e.g., shifting assets between stocks, bonds, or crypto).<br />

[ ] new loan/fraud check/update with start <br />
[ ] financial advise - args being freeform customer input about their financial situation, goals
    [ ] tool is maybe a new tool asking the LLM to advise

[ ] for demo simulate failure  - add utilities/simulated failures from pipeline demo <br />

[ ] LLM failure->autoswitch: <br />
    - detect failure in the activity using failurecount <br />
    - activity switches to secondary LLM defined in .env
    - activity reports switch to workflow

[ ] for demo simulate failure  - add utilities/simulated failures from pipeline demo <br />

[ ] expand [tests](./tests/agent_goal_workflow_test.py)<br />
[ ] collapse history/summarize after goal finished <br />
[ ] add aws bedrock <br />

[ ] ask the ai agent how it did at the end of the conversation, was it efficient? successful? insert a search attribute to document that before return <br />
- Insight into the agent’s performance <br />
[ ] non-retry the api key error - "Invalid API Key provided: sk_test_**J..." and "AuthenticationError" <br />
[ ] add visual feedback when workflow starting <br />
[ ] enable user to list agents at any time - like end conversation - probably with a next step<br />
 - with changing "'Next should only be "pick-new-goal" if all tools have been run (use the system prompt to figure that out).'" in [prompt_generators](./prompts/agent_prompt_generators.py).