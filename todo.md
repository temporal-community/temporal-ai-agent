# todo list
[ ] add confirmation env setting to setup guide <br />
 <br />
[x] how to add more scenarios, tools <br />
[ ] make agent respond to name of goals and not just numbers
[ ] L look at slides
[ ] josh to do fintech scenarios
[ ] create tests<br />
[ ] fix logging statements not to be all warn, maybe set logging level to info

[ ] create people management scenarios <br />

[ ] 2. Others HR goals:
-- book work travel <br />
-- check insurance coverages <br />
-- expense management <br />
-- check in on the health of the team <br />

[x] demo the reasons why: <br />
- Orchestrate interactions across distributed data stores and tools <br />
- Hold state, potentially over long periods of time <br />
- Ability to ‘self-heal’ and retry until the (probabilistic) LLM returns valid data <br />
- Support for human intervention such as approvals <br />
- Parallel processing for efficiency of data retrieval and tool use <br />

[ ] ask the ai agent how it did at the end of the conversation, was it efficient? successful? insert a search attribute to document that before return
- Insight into the agent’s performance <br />

[x] customize prompts in [workflow to manage scenario](./workflows/tool_workflow.py)<br />
[x] add in new tools? <br />

[ ] non-retry the api key error - "Invalid API Key provided: sk_test_**J..." and "AuthenticationError" <br />
[ ] make it so you can yeet yourself out of a goal and pick a new one <br />

[ ] add visual feedback when workflow starting <br />
[ ] figure out how to allow user to list agents at any time - like end conversation <br />