# Architecture Decisions

## Table of Contents
- [AI Models](#ai-models)
- [Temporal](#temporal)
  - [Reliability and State Management](#reliability-and-state-management)
  - [Handling Complex, Dynamic Workflows](#handling-complex-dynamic-workflows)
  - [Scalability and Speed](#scalability-and-speed)
  - [Observability and Debugging](#observability-and-debugging)
  - [Simplified Error Handling](#simplified-error-handling)
  - [Flexibility for Experimentation](#flexibility-for-experimentation)

This documents some of the "why" behind the [architecture](./architecture.md). 

## AI Models
We wanted to have flexibility to use different models, because this space is changing rapidly and models get better regularly.
Also, for you, we wanted to let you pick your model of choice. The system is designed to make changing models out simple. For how to do that, checkout the [setup guide](./setup.md).

## Temporal
We asked one of the AI models used in this demo to answer this question (edited minorly):

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

In this system Temporal lets you:
- Orchestrate interactions across distributed data stores and tools <br />
- Hold state, potentially over long periods of time <br />
- Ability to ‘self-heal’ and retry until the (probabilistic) LLM returns valid data <br />
- Support for human intervention such as approvals <br />
- Parallel processing for efficiency of data retrieval and tool use <br />