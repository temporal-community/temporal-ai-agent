# todo list
[x] clean up workflow/make functions

[x] make the debugging confirms optional <br />
[ ] add confirmation env setting to setup guide <br />
 <br />
[x] document *why* temporal for ai agents - scalability, durability, visibility in the readme <br />
[x] fix readme: move setup to its own page, demo to its own page, add the why /|\ section <br />
[x] add architecture to readme <br />
- elements of app <br />
- dive into llm interaction <br />
- workflow breakdown - interactive loop <br />
- why temporal <br />

[x] setup readme, why readme, architecture readme, what this is in main readme with temporal value props and pictures <br />
[ ] how to add more scenarios, tools <br />

[ ] create tests<br />
[ ] fix logging statements not to be all warn, maybe set logging level to info

[ ] create people management scenarios <br />
[x] 1. Schedule PTO goal
-- [ ] check current PTO level <br />
-- [ ] determine PTO available as of date <br />
-- [ ] check for personal, team, or both calendar conflicts <br />
-- [ ] book PTO around a date (send calendar invite?) (https://developers.google.com/calendar/api/guides/overview)? <br />
[ ] 2. Others:
-- check pay status <br />
-- book work travel <br />
-- check insurance coverages <br />
-- expense management <br />
-- check in on the health of the team <br />

[ ] demo the reasons why: <br />
- Orchestrate interactions across distributed data stores and tools <br />
- Hold state, potentially over long periods of time <br />
- Ability to ‘self-heal’ and retry until the (probabilistic) LLM returns valid data <br />
- Support for human intervention such as approvals <br />
- Parallel processing for efficiency of data retrieval and tool use <br />
- Insight into the agent’s performance <br />
    - ask the ai agent how it did at the end of the conversation, was it efficient? successful? insert a search attribute to document that before return

[ ] customize prompts in [workflow to manage scenario](./workflows/tool_workflow.py)<br />
[ ] add in new tools? <br />

[ ] non-retry the api key error - "Invalid API Key provided: sk_test_**J..." and "AuthenticationError" <br />
[ ] make it so you can yeet yourself out of a goal and pick a new one <br />

[ ] add visual feedback when workflow starting <br />
[ ] figure out how to allow user to list agents at any time - like end conversation <br />