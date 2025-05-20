# Temporal AI Agent

This demo shows a multi-turn conversation with an AI agent running inside a Temporal workflow. The purpose of the agent is to collect information towards a goal, running tools along the way. There's a simple DSL input for collecting information (currently set up to use mock functions to search for public events, search for flights around those events, then create a test Stripe invoice for the trip).

The AI will respond with clarifications and ask for any missing information to that goal. You can configure it to use any LLM supported by [LiteLLM](https://docs.litellm.ai/docs/providers), including:
- OpenAI models (GPT-4, GPT-3.5)
- Anthropic Claude models
- Google Gemini models
- Deepseek models
- Ollama models (local)
- And many more!

It's really helpful to [watch the demo (5 minute YouTube video)](https://www.youtube.com/watch?v=GEXllEH2XiQ) to understand how interaction works.

[![Watch the demo](./assets/agent-youtube-screenshot.jpeg)](https://www.youtube.com/watch?v=GEXllEH2XiQ)

### Multi-Agent Demo Video
See multi-agent execution in action [here](https://www.youtube.com/watch?v=8Dc_0dC14yY).

## Why Temporal?
There are a lot of AI and Agentic AI tools out there, and more on the way. But why Temporal? Temporal gives this system reliablity, state management, a code-first approach that we really like, built-in observability and easy error handling.
For more, check out [architecture-decisions](./architecture-decisions.md).

## What is "Agentic AI"?
These are the key elements of an agentic framework:
1. Goals that a system can accomplish, made up of tools that can execute individual steps
2. Agent loops - executing an LLM, executing tools, and eliciting input from an external source such as a human: repeat until goal(s) are done
3. Support for tool calls that require input and approval
4. Use of an LLM to check human input for relevance before calling the 'real' LLM
5. Use of an LLM to summarize and compact the conversation history
6. Prompt construction made of system prompts, conversation history, and tool metadata - sent to the LLM to create user questions and confirmations
7. Ideally high durability (done in this system with Temporal Workflow and Activities)

For a deeper dive into this, check out the [architecture guide](./architecture.md).

## Setup and Configuration
See [the Setup guide](./setup.md) for detailed instructions. The basic configuration requires just two environment variables:
```bash
LLM_MODEL=openai/gpt-4o  # or any other model supported by LiteLLM
LLM_KEY=your-api-key-here
```

## Customizing Interaction & Tools
See [the guide to adding goals and tools](./adding-goals-and-tools.md).

## Architecture
See [the architecture guide](./architecture.md).

## Productionalization & Adding Features
- In a prod setting, I would need to ensure that payload data is stored separately (e.g. in S3 or a noSQL db - the claim-check pattern), or otherwise 'garbage collected'. Without these techniques, long conversations will fill up the workflow's conversation history, and start to breach Temporal event history payload limits.
- A single worker can easily support many agent workflows (chats) running at the same time. Currently the workflow ID is the same each time, so it will only run one agent at a time. To run multiple agents, you can use a different workflow ID each time (e.g. by using a UUID or timestamp).
- Perhaps the UI should show when the LLM response is being retried (i.e. activity retry attempt because the LLM provided bad output)
- Tests would be nice! [See tests](./tests/).


See [the todo](./todo.md) for more details.

See [the guide to adding goals and tools](./adding-goals-and-tools.md) for more ways you can add features.

## Enablement Guide (internal resource for Temporal employees)
Check out the [slides](https://docs.google.com/presentation/d/1wUFY4v17vrtv8llreKEBDPLRtZte3FixxBUn0uWy5NU/edit#slide=id.g3333e5deaa9_0_0) here and the [enablement guide](https://docs.google.com/document/d/14E0cEOibUAgHPBqConbWXgPUBY0Oxrnt6_AImdiheW4/edit?tab=t.0#heading=h.ajnq2v3xqbu1).


