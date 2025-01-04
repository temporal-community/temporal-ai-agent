# AI Agent execution using Temporal

Work in progress.

This demo shows a multi-turn conversation with an AI agent running inside a Temporal workflow. The goal is to collect information towards a goal. There's a simple DSL input for collecting information (currently set up to use mock functions to search for events, book flights around those events then generate an invoice for those flights, see `send_message.py`). The AI will respond with clarifications and ask for any missing information to that goal. It uses a local LLM via Ollama.

## Setup
* Requires an OpenAI key for the gpt-4o model. Set this in the `OPENAI_API_KEY` environment variable in .env
* Requires a rapidapi key for sky-scrapper (how we find flights). Set this in the `RAPIDAPI_KEY` environment variable in .env
    * If you're lazy go to `tools/search_flights.py` and replace the `get_flights` function with the mock `search_flights_example` that exists in the same file.
* See .env_example for the required environment variables.
* Install and run Temporal. Follow the instructions in the [Temporal documentation](https://learn.temporal.io/getting_started/python/dev_environment/#set-up-a-local-temporal-service-for-development-with-temporal-cli) to install and run the Temporal server.
* Install the dependencies: `poetry install`

Deprecated:
* Install [Ollama](https://ollama.com) and the [Qwen2.5 14B](https://ollama.com/library/qwen2.5) model (`ollama run qwen2.5:14b`). (note this model is about 9GB to download).
  * Local LLM is disabled as ChatGPT 4o was better for this use case. To use Ollama, examine `./activities/tool_activities.py` and rename the functions.

## Running the example

From the /scripts directory:

1. Run the worker: `poetry run python run_worker.py`
2. In another terminal run the client with a prompt.

    Example: `poetry run python send_message.py 'Can you find events in march in oceania?'`

3. View the worker's output for the response.
4. Give followup prompts by signaling the workflow.

    Example: `poetry run python send_message.py 'I want to fly from San Francisco'`

    NOTE: The workflow will pause on the 'confirm' step until the user sends a 'confirm' signal. Use `poetry run python get_tool_data.py` query to see the current state of the workflow.

    You can send a 'confirm' signal using `poetry run python send_confirm.py`
5. Get the conversation history summary by querying the workflow.
    
    Example: `poetry run python get_history.py`
6. To end the chat session, run `poetry run python end_chat.py`

The chat session will end if it has collected enough information to complete the task or if the user explicitly ends the chat session.

Run query get_tool_data to see the data the tool has collected so far.

## API
- `poetry run uvicorn api.main:app --reload` to start the API server.
- Access the API at `/docs` to see the available endpoints.

## UI
TODO: Document /frontend react app running instructions.

## Customizing the agent
- `tool_registry.py` contains the mapping of tool names to tool definitions (so the AI understands how to use them)
- The tools themselves are defined in their own files in `/tools`
- Note the mapping in `tools/__init__.py` to each tool

## TODO
- Code GenerateInvoice against the Stripe API
- I should prove this out with other tool definitions outside of the event/flight search case (take advantage of my nice DSL).
- Currently hardcoded to the Temporal dev server at localhost:7233. Need to support options incl Temporal Cloud.
- UI: Make prettier
- UI: Tool Confirmed state could be better represented