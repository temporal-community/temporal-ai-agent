# AI Agent execution using Temporal

Work in progress.

This demo shows a multi-turn conversation with an AI agent running inside a Temporal workflow. The goal is to collect information towards a goal. There's a simple DSL input for collecting information (currently set up to use mock functions to search for events, book flights around those events then generate an invoice for those flights, see `send_message.py`). The AI will respond with clarifications and ask for any missing information to that goal. It uses a local LLM via Ollama.

## Setup
* Install [Ollama](https://ollama.com) and the Mistral model (`ollama run qwen2.5:14b`). (note this model is more than 10GB to download).
* Install and run Temporal. Follow the instructions in the [Temporal documentation](https://learn.temporal.io/getting_started/python/dev_environment/#set-up-a-local-temporal-service-for-development-with-temporal-cli) to install and run the Temporal server.
* Install the dependencies: `poetry install`

## Running the example

From the /scripts directory:

1. Run the worker: `poetry run python run_worker.py`
2. In another terminal run the client with a prompt.

    Example: `poetry run python send_message.py 'Can you find events in march in oceania?'`

3. View the worker's output for the response.
4. Give followup prompts by signaling the workflow.

    Example: `poetry run python send_message.py 'sure, book flights'`
5. Get the conversation history summary by querying the workflow.
    
    Example: `poetry run python get_history.py`
6. To end the chat session, run `poetry run python end_chat.py`

The chat session will end if it has collected enough information to complete the task or if the user explicitly ends the chat session.

Run query get_tool_data to see the data the tool has collected so far.

## TODO
- The LLM prompts move through 3 mock tools (FindEvents, SearchFlights, CreateInvoice) but I should make them contact real APIs.
- I need to add a human in the loop confirmation step before it executes any tools.
- I need to build a chat interface so it's not cli-controlled. Also want to show some 'behind the scenes' of the agents being used as they run.