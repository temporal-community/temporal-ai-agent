# Temporal AI Agent

This demo shows a multi-turn conversation with an AI agent running inside a Temporal workflow. The purpose of the agent is to collect information towards a goal, running tools along the way. There's a simple DSL input for collecting information (currently set up to use mock functions to search for public events, search for flights around those events, then create a test Stripe invoice for the trip).

The AI will respond with clarifications and ask for any missing information to that goal. You can configure it to use [ChatGPT 4o](https://openai.com/index/hello-gpt-4o/), [Anthropic Claude](https://www.anthropic.com/claude), [Google Gemini](https://gemini.google.com), [Deepseek-V3](https://www.deepseek.com/), [Grok](https://docs.x.ai/docs/overview) or a local LLM of your choice using [Ollama](https://ollama.com).

It's really helpful to [watch the demo (5 minute YouTube video)](https://www.youtube.com/watch?v=GEXllEH2XiQ) to understand how interaction works.

[![Watch the demo](./assets/agent-youtube-screenshot.jpeg)](https://www.youtube.com/watch?v=GEXllEH2XiQ)

## Why Temporal?
There are a lot of AI and Agentic AI tools out there, and more on the way. But why Temporal? Temporal gives this system reliablity, state management, a code-first approach that we really like, built-in observability and easy error handling.
For more, check out [architecture-decisions](./architecture-decisions.md).

## What is "Agentic AI"?
These are the key elements of an agentic framework:
1. Goals a human can get done, made up of tools that can execute individual steps
2. The "agent loop" - call LLM, either call tools or prompt human, repeat until goal(s) are done
3. Support for tool calls that require human input and approval
4. Use of an LLM to check human input for relevance before calling the 'real' LLM
5. use of an LLM to summarize and compact the conversation history
6. Prompt construction (made of system prompts, conversation history, and tool metadata - sent to the LLM to create user prompts)
7. Bonus: durable tool execution via Temporal Activities

For a deeper dive into this, check out the [architecture guide](./architecture.md).

## Setup and Configuration
See [the Setup guide](./setup.md).

## Customizing Interaction & Tools
See [the guide to adding goals and tools](./adding-goals-and-tools.md).

## Architecture
See [the architecture guide](./architecture.md).

## Productionalization & Adding Features
- In a prod setting, I would need to ensure that payload data is stored separately (e.g. in S3 or a noSQL db - the claim-check pattern), or otherwise 'garbage collected'. Without these techniques, long conversations will fill up the workflow's conversation history, and start to breach Temporal event history payload limits.
- A single worker can easily support many workflows - setting workflow ID differently would enable this.
- Continue-as-new shouldn't be a big consideration for this use case (as it would take many conversational turns to trigger). Regardless, we should verify that it's able to carry the agent state over to the new workflow execution.
- Perhaps the UI should show when the LLM response is being retried (i.e. activity retry attempt because the LLM provided bad output)
- Tests would be nice! [See tests](./tests/).


See [the todo](./todo.md) for more details.

See [the guide to adding goals and tools](./adding-goals-and-tools.md) for more ways you can add features.

## For Temporal SAs
Check out the [slides](https://docs.google.com/presentation/d/1wUFY4v17vrtv8llreKEBDPLRtZte3FixxBUn0uWy5NU/edit#slide=id.g3333e5deaa9_0_0) here and the enablement guide here (TODO).

## Tests

Running the tests requires `poe` and `pytest_asyncio` to be installed.

    python -m pip install poethepoet
    python -m pip install pytest_asyncio

Once you have `poe` and `pytest_asyncio` installed you can run:

    poe test
