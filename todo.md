# todo list

## General Agent Enhancements

[ ] MCP: There is a plan to add MCP (Model Context Protocol) to the agent. This really really really needs to be done and is scheduled to be done by @steveandroulakis some time in June 2025.

[ ] Google's A2A is emerging as the standard way to hand off agents to other agents. We should examine implementing this soon.

[ ] Custom metrics/tracing is important for AI specific aspects such as number of LLM calls, number of bad LLM responses that require retrying, number of bad chat outcomes. We should add this.

[ ] Evals are very important in agents. We want to be able to 'judge' the agent's performance both in dev and production (AIOps). This will help us improve our agent's performance over time in a targeted fashion.

[ ] Dynamically switch LLMs on persistent failures: <br />
    - detect failure in the activity using failurecount <br />
    - activity switches to secondary LLM defined in .env
    - activity reports switch to workflow

[ ] Collapse history/summarize chat after goal finished <br />

[ ] Write tests<br />

[ ] non-retry the api key error - "Invalid API Key provided: sk_test_**J..." and "AuthenticationError" <br />

[ ] add visual feedback when workflow starting <br />

[ ] enable user to list agents at any time - like end conversation - probably with a next step<br />

## Ideas for more goals and tools

[ ] Add fintech goals <br />
- Fraud Detection and Prevention - The AI monitors transactions across accounts, flagging suspicious activities (e.g., unusual spending patterns or login attempts) and autonomously freezing accounts or notifying customers and compliance teams.<br />
- Personalized Financial Advice - An AI agent analyzes a customer’s financial data (e.g., income, spending habits, savings, investments) and provides tailored advice, such as budgeting tips, investment options, or debt repayment strategies.<br />
- Portfolio Management and Rebalancing - The AI monitors a customer’s investment portfolio, rebalancing it automatically based on market trends, risk tolerance, and financial goals (e.g., shifting assets between stocks, bonds, or crypto).<br />

[ ] new loan/fraud check/update with start <br />
[ ] financial advise - args being freeform customer input about their financial situation, goals
    [ ] tool is maybe a new tool asking the LLM to advise

[ ] for demo simulate failure  - add utilities/simulated failures from pipeline demo <br />
