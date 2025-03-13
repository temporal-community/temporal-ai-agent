# Temporal AI Agent

This demo shows a multi-turn conversation with an AI agent running inside a Temporal workflow. The purpose of the agent is to collect information towards a goal, running tools along the way. There's a simple DSL input for collecting information (currently set up to use mock functions to search for public events, search for flights around those events, then create a test Stripe invoice for the trip).

The AI will respond with clarifications and ask for any missing information to that goal. You can configure it to use [ChatGPT 4o](https://openai.com/index/hello-gpt-4o/), [Anthropic Claude](https://www.anthropic.com/claude), [Google Gemini](https://gemini.google.com), [Deepseek-V3](https://www.deepseek.com/), [Grok](https://docs.x.ai/docs/overview) or a local LLM of your choice using [Ollama](https://ollama.com).

It's really helpful to [watch the demo (5 minute YouTube video)](https://www.youtube.com/watch?v=GEXllEH2XiQ) to understand how interaction works.

[![Watch the demo](./assets/agent-youtube-screenshot.jpeg)](https://www.youtube.com/watch?v=GEXllEH2XiQ)

## Why Temporal?
There are a lot of AI and Agentic AI tools out there, and more on the way. But why Temporal? I asked one of the AI models used in this demo to answer this question (edited minorly):

### Reliability and State Management:
 Temporal ensures durability and fault tolerance, which are critical for agentic AI systems that involve long-running, complex workflows. For example, it preserves application state across failures, allowing AI agents to resume from where they left off without losing progress. Major AI companies use this for research experiments and agentic flows, where reliability is essential for continuous exploration.
### Handling Complex, Dynamic Workflows: 
Agentic AI often involves unpredictable, multi-step processes like web crawling or data searching. Temporal’s workflow orchestration simplifies managing these tasks by abstracting complexity, providing features like retries, timeouts, and signals/queries. Temporal makes observability and resuming failed complex experiments and deep searches simple.
### Scalability and Speed: 
Temporal enables rapid development and scaling, crucial for AI systems handling large-scale experiments or production workloads. AI model deployment and SRE teams use it to get code to production quickly with scale as a focus, while research teams can (and do!) run hundreds of experiments daily. Temporal customers report a significant reduction in development time (e.g., 20 weeks to 2 weeks for a feature).
### Observability and Debugging: 
Agentic AI systems need insight into where processes succeed or fail. Temporal provides end-to-end visibility and durable workflow history, which Temporal customers are using to track agentic flows and understand failure points.
### Simplified Error Handling: 
Temporal abstracts failure management (e.g., retries, rollbacks) so developers can focus on AI logic rather than "plumbing" code. This is vital for agentic AI, where external interactions (e.g., APIs, data sources) are prone to failure.
### Flexibility for Experimentation: 
For research-heavy agentic AI, Temporal supports dynamic, code-first workflows and easy integration of new signals/queries, aligning with researchers needs to iterate quickly on experimental paths.

In essence, Temporal’s value lies in its ability to make agentic AI systems more reliable, scalable, and easier to develop by handling the underlying complexity of distributed workflows for both research and applied AI tasks.

Temporal was built to solve the problems of distributed computing, including scalability, reliability, security, visibility, and complexity. Agentic AI systems are complex distributed systems, so Temporal should fit well. Scaling, security, and productionalization are major pain points in March 2025 for building agentic systems.

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
