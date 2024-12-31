# AI Agent execution using Temporal

Work in progress (very early!).

This demo shows a multi-turn conversation with an AI agent running inside a Temporal workflow. The goal is to collect information towards a goal. There's a simple DSL input for collecting information (currently set up to search for flights, see `send_message.py`). The AI will respond with clarifications and ask for any missing information (e.g., origin city, destination, travel dates). It uses a local LLM via Ollama.

## Setup
* Install [Ollama](https://ollama.com) and the Mistral model (`ollama run qwen2.5:14b`). (note this model is more than 10GB to download).
* Install and run Temporal. Follow the instructions in the [Temporal documentation](https://learn.temporal.io/getting_started/python/dev_environment/#set-up-a-local-temporal-service-for-development-with-temporal-cli) to install and run the Temporal server.
* Install the dependencies: `poetry install`

## Running the example

1. Run the worker: `poetry run python run_worker.py`
2. In another terminal run the client with a prompt.

    Example: `poetry run python send_message.py 'I want to book a flight'`

3. View the worker's output for the response.
4. Give followup prompts by signaling the workflow.

    Example: `poetry run python send_message.py 'From San Francisco'`
5. Get the conversation history summary by querying the workflow.
    
    Example: `poetry run python get_history.py`
6. To end the chat session, run `poetry run python end_chat.py`

The chat session will end if it has collected enough information to complete the task or if the user explicitly ends the chat session.

Run query get_tool_data to see the data the tool has collected so far.

## TODO
- This is currently a good single tool workflow. It could be a child as part of a planning workflow (multiple tools).
- I should integrate another tool. Perhaps something that consumes web sites hunting for destinations to go to in the first place.
- I should make this workflow execute a Search for flights as right now it will finish without doing anything.
- I need to add a human in the loop confirmation step before it executes tools.
- I need to build a chat interface so it's not cli-controlled. Also want to show some 'behind the scenes' of the agents being used as they run.