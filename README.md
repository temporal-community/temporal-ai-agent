# Temporal AI Agent

This demo shows a multi-turn conversation with an AI agent running inside a Temporal workflow. The purpose of the agent is to collect information towards a goal, running tools along the way. There's a simple DSL input for collecting information (currently set up to use mock functions to search for public events, search for flights around those events, then create a test Stripe invoice for the trip).

The AI will respond with clarifications and ask for any missing information to that goal. You can configure it to use [ChatGPT 4o](https://openai.com/index/hello-gpt-4o/), [Anthropic Claude](https://www.anthropic.com/claude), [Google Gemini](https://gemini.google.com), [Deepseek-V3](https://www.deepseek.com/) or a local LLM of your choice using [Ollama](https://ollama.com).

[Watch the demo (5 minute YouTube video)](https://www.youtube.com/watch?v=GEXllEH2XiQ)

[![Watch the demo](./agent-youtube-screenshot.jpeg)](https://www.youtube.com/watch?v=GEXllEH2XiQ)

## Configuration

This application uses `.env` files for configuration. Copy the [.env.example](.env.example) file to `.env` and update the values:

```bash
cp .env.example .env
```

### Agent Goal Configuration

The agent can be configured to pursue different goals using the `AGENT_GOAL` environment variable in your `.env` file.

#### Goal: Find an event in Australia / New Zealand, book flights to it and invoice the user for the cost
- `AGENT_GOAL=goal_event_flight_invoice` (default) - Helps users find events, book flights, and arrange train travel with invoice generation
    - This is the scenario in the video above

#### Goal: Find a Premier League match, book train tickets to it and invoice the user for the cost
- `AGENT_GOAL=goal_match_train_invoice` - Focuses on Premier League match attendance with train booking and invoice generation
    - This goal was part of [Temporal's Replay 2025 conference keynote demo](https://www.youtube.com/watch?v=YDxAWrIBQNE)
    - Note, there is failure built in to this demo (the train booking step) to show how the agent can handle failures and retry. See Tool Configuration below for details.

If not specified, the agent defaults to `goal_event_flight_invoice`. Each goal comes with its own set of tools and conversation flows designed for specific use cases. You can examine `tools/goal_registry.py` to see the detailed configuration of each goal.

See the next section for tool configuration for each goal.

### Tool Configuration

#### Agent Goal: goal_event_flight_invoice (default)
* The agent uses a mock function to search for events. This has zero configuration.
* By default the agent uses a mock function to search for flights.
    * If you want to use the real flights API, go to `tools/search_flights.py` and replace the `search_flights` function with `search_flights_real_api` that exists in the same file.
    * It's free to sign up at [RapidAPI](https://rapidapi.com/apiheya/api/sky-scrapper)
    * This api might be slow to respond, so you may want to increase the start to close timeout, `TOOL_ACTIVITY_START_TO_CLOSE_TIMEOUT` in `workflows/workflow_helpers.py`
* Requires a Stripe key for the `create_invoice` tool. Set this in the `STRIPE_API_KEY` environment variable in .env
    * It's free to sign up and get a key at [Stripe](https://stripe.com/)
        * Set permissions for read-write on: `Credit Notes, Invoices, Customers and Customer Sessions`
    * If you're lazy go to `tools/create_invoice.py` and replace the `create_invoice` function with the mock `create_invoice_example` that exists in the same file.

#### Agent Goal: goal_match_train_invoice
NOTE: This goal was developed for an on-stage demo and has failure (and its resolution) built in to show how the agent can handle failures and retry.
* Finding a match requires a key from [Football Data](https://www.football-data.org). Sign up for a free account, then see the 'My Account' page to get your API token. Set `FOOTBALL_DATA_API_KEY` to this value.
    * If you're lazy go to `tools/search_fixtures.py` and replace the `search_fixtures` function with the mock `search_fixtures_example` that exists in the same file.
* We use a mock function to search for trains. Start the train API server to use the real API: `python thirdparty/train_api.py`
* * The train activity is 'enterprise' so it's written in C# and requires a .NET runtime. See the [.NET backend](#net-(enterprise)-backend) section for details on running it.
* Requires a Stripe key for the `create_invoice` tool. Set this in the `STRIPE_API_KEY` environment variable in .env
    * It's free to sign up and get a key at [Stripe](https://stripe.com/)
    * If you're lazy go to `tools/create_invoice.py` and replace the `create_invoice` function with the mock `create_invoice_example` that exists in the same file.

### LLM Provider Configuration

The agent can use OpenAI's GPT-4o, Google Gemini, Anthropic Claude, or a local LLM via Ollama. Set the `LLM_PROVIDER` environment variable in your `.env` file to choose the desired provider:

- `LLM_PROVIDER=openai` for OpenAI's GPT-4o
- `LLM_PROVIDER=google` for Google Gemini
- `LLM_PROVIDER=anthropic` for Anthropic Claude
- `LLM_PROVIDER=deepseek` for DeepSeek-V3
- `LLM_PROVIDER=ollama` for running LLMs via [Ollama](https://ollama.ai) (not recommended for this use case)

### Option 1: OpenAI

If using OpenAI, ensure you have an OpenAI key for the GPT-4o model. Set this in the `OPENAI_API_KEY` environment variable in `.env`.

### Option 2: Google Gemini

To use Google Gemini:

1. Obtain a Google API key and set it in the `GOOGLE_API_KEY` environment variable in `.env`.
2. Set `LLM_PROVIDER=google` in your `.env` file.

### Option 3: Anthropic Claude (recommended)

I find that Claude Sonnet 3.5 performs better than the other hosted LLMs for this use case.

To use Anthropic:

1. Obtain an Anthropic API key and set it in the `ANTHROPIC_API_KEY` environment variable in `.env`.
2. Set `LLM_PROVIDER=anthropic` in your `.env` file.

### Option 4: Deepseek-V3

To use Deepseek-V3:

1. Obtain a Deepseek API key and set it in the `DEEPSEEK_API_KEY` environment variable in `.env`.
2. Set `LLM_PROVIDER=deepseek` in your `.env` file.

### Option 5: Local LLM via Ollama (not recommended)

To use a local LLM with Ollama:

1. Install [Ollama](https://ollama.com) and the [Qwen2.5 14B](https://ollama.com/library/qwen2.5) model.
   - Run `ollama run <OLLAMA_MODEL_NAME>` to start the model. Note that this model is about 9GB to download.
   - Example: `ollama run qwen2.5:14b`

2. Set `LLM_PROVIDER=ollama` in your `.env` file and `OLLAMA_MODEL_NAME` to the name of the model you installed.

Note: I found the other (hosted) LLMs to be MUCH more reliable for this use case. However, you can switch to Ollama if desired, and choose a suitably large model if your computer has the resources.

## Configuring Temporal Connection

By default, this application will connect to a local Temporal server (`localhost:7233`) in the default namespace, using the `agent-task-queue` task queue. You can override these settings in your `.env` file.

### Use Temporal Cloud

See [.env.example](.env.example) for details on connecting to Temporal Cloud using mTLS or API key authentication.

[Sign up for Temporal Cloud](https://temporal.io/get-cloud)

### Use a local Temporal Dev Server

On a Mac
```bash
brew install temporal
temporal server start-dev
```
See the [Temporal documentation](https://learn.temporal.io/getting_started/python/dev_environment/) for other platforms.


## Running the Application
### Development with Docker
- All services are defined in `docker-compose.yml`.
- **Dev overrides** (mounted code, live‑reload commands) live in `docker-compose.override.yml` and are **auto‑merged** on `docker compose up`.
- To start **development** mode (with hot‑reload):
  ```bash
  docker compose up -d
  # quick rebuild without infra:
  docker compose up -d --no-deps --build api train-api worker frontend
  ```
- To run **production** mode (ignore dev overrides):
  ```bash
  docker compose -f docker-compose.yml up -d
  ```

### Python Backend
Requires [Poetry](https://python-poetry.org/) to manage dependencies.

1. `python -m venv venv`

2. `source venv/bin/activate`

3. `poetry install`

Run the following commands in separate terminal windows:

1. Start the Temporal worker:
```bash
poetry run python scripts/run_worker.py
```

2. Start the API server:
```bash
poetry run uvicorn api.main:app --reload
```
Access the API at `/docs` to see the available endpoints.

### React UI
Start the frontend:
```bash
cd frontend
npm install
npx vite
```
Access the UI at `http://localhost:5173`

### Python Search Trains API
> Agent Goal: goal_match_train_invoice only

Required to search and book trains!
```bash
poetry run python thirdparty/train_api.py

# example url
# http://localhost:8080/api/search?from=london&to=liverpool&outbound_time=2025-04-18T09:00:00&inbound_time=2025-04-20T09:00:00
```

### Python Train Legacy Worker
> Agent Goal: goal_match_train_invoice only

These are Python activities that fail (raise NotImplemented) to show how Temporal handles a failure. You can run these activities with.

```bash
poetry run python scripts/run_legacy_worker.py 
```

The activity will fail and be retried infinitely. To rescue the activity (and its corresponding workflows), kill the worker and run the .NET one in the section below.

### .NET (enterprise) Worker ;)
> Agent Goal: goal_match_train_invoice only

We have activities written in C# to call the train APIs.
```bash
cd enterprise
dotnet build # ensure you brew install dotnet@8 first!
dotnet run
```
If you're running your train API above on a different host/port then change the API URL in `Program.cs`. Otherwise, be sure to run it using `python thirdparty/train_api.py`.

## Customizing the Agent
- `tool_registry.py` contains the mapping of tool names to tool definitions (so the AI understands how to use them)
- `goal_registry.py` contains descriptions of goals and the tools used to achieve them
- The tools themselves are defined in their own files in `/tools`
- Note the mapping in `tools/__init__.py` to each tool

## TODO
- In a prod setting, I would need to ensure that payload data is stored separately (e.g. in S3 or a noSQL db - the claim-check pattern), or otherwise 'garbage collected'. Without these techniques, long conversations will fill up the workflow's conversation history, and start to breach Temporal event history payload limits.
- Continue-as-new shouldn't be a big consideration for this use case (as it would take many conversational turns to trigger). Regardless, I should ensure that it's able to carry the agent state over to the new workflow execution.
- Perhaps the UI should show when the LLM response is being retried (i.e. activity retry attempt because the LLM provided bad output)
- Tests would be nice!
