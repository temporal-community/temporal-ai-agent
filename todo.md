# todo list
[ ] expand [tests](./tests/agent_goal_workflow_test.py)<br />

[ ] adding fintech goals <br />
- Fraud Detection and Prevention - The AI monitors transactions across accounts, flagging suspicious activities (e.g., unusual spending patterns or login attempts) and autonomously freezing accounts or notifying customers and compliance teams.<br />
- Personalized Financial Advice - An AI agent analyzes a customer’s financial data (e.g., income, spending habits, savings, investments) and provides tailored advice, such as budgeting tips, investment options, or debt repayment strategies.<br />
- Portfolio Management and Rebalancing - The AI monitors a customer’s investment portfolio, rebalancing it automatically based on market trends, risk tolerance, and financial goals (e.g., shifting assets between stocks, bonds, or crypto).<br />

[ ] new loan/fraud check/update with start <br />
[ ] financial advise - args being freeform customer input about their financial situation, goals
    [ ] tool is maybe a new tool asking the LLM to advise

[ ] LLM failure->autoswitch: <br />
    - detect failure in the activity using failurecount <br />
    - activity switches to secondary LLM defined in .env
    - activity reports switch to workflow

[ ] ask the ai agent how it did at the end of the conversation, was it efficient? successful? insert a search attribute to document that before return <br />
- Insight into the agent’s performance <br />
[ ] non-retry the api key error - "Invalid API Key provided: sk_test_**J..." and "AuthenticationError" <br />
[ ] add visual feedback when workflow starting <br />
[ ] enable user to list agents at any time - like end conversation - probably with a next step<br />
 - with changing "'Next should only be "pick-new-goal" if all tools have been run (use the system prompt to figure that out).'" in [prompt_generators](./prompts/agent_prompt_generators.py).