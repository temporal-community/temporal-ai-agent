# todo list
[ ] multi-goal <br />
    [x] set goal to list agents when done <br />
    [ ] make this better/smoother <br />

[ ] make the debugging confirms optional <br />
[ ] grok integration <br />
[ ] document *why* temporal for ai agents - scalability, durability in the readme <br />
[ ] fix readme: move setup to its own page, demo to its own page, add the why /|\ section <br />
[ ] add architecture to readme <br />
[ ] create tests<br />

[ ] create people management scenario <br />
  -- check pay status
  -- book work travel
  -- check PTO levels
  -- check insurance coverages
  -- book PTO around a date (https://developers.google.com/calendar/api/guides/overview)? 
  -- scenario should use multiple tools
  -- expense management
  -- check in on the health of the team
[ ] demo the reasons why:
  -- Orchestrate interactions across distributed data stores and tools
  -- Hold state, potentially over long periods of time
  -- Ability to ‘self-heal’ and retry until the (probabilistic) LLM returns valid data
  -- Support for human intervention such as approvals
  -- Parallel processing for efficiency of data retrieval and tool use
  -- Insight into the agent’s performance

[ ] customize prompts in [workflow to manage scenario](./workflows/tool_workflow.py)<br />
[ ] add in new tools? <br />

[ ] non-retry the api key error - "Invalid API Key provided: sk_test_**J..." and "AuthenticationError"

