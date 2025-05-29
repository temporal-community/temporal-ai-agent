# Setup Guide
## Initial Configuration

This application uses `.env` files for configuration. Copy the [.env.example](.env.example) file to `.env` and update the values:

```bash
cp .env.example .env
```

Then add API keys, configuration, as desired.

If you want to show confirmations/enable the debugging UI that shows tool args, set
```bash
SHOW_CONFIRM=True
```

### Quick Start with Makefile

We've provided a Makefile to simplify the setup and running of the application. Here are the main commands:

```bash
# Initial setup
make setup              # Creates virtual environment and installs dependencies
make setup-venv         # Creates virtual environment only
make install            # Installs all dependencies

# Running the application
make run-worker         # Starts the Temporal worker
make run-api            # Starts the API server
make run-frontend       # Starts the frontend development server

# Additional services
make run-train-api      # Starts the train API server
make run-legacy-worker  # Starts the legacy worker
make run-enterprise     # Builds and runs the enterprise .NET worker

# Development environment setup
make setup-temporal-mac # Installs and starts Temporal server on Mac

# View all available commands
make help
```

### Manual Setup (Alternative to Makefile)

If you prefer to run commands manually, follow these steps:

### Agent Goal Configuration

The agent can be configured to pursue different goals using the `AGENT_GOAL` environment variable in your `.env` file. If unset, default is `goal_choose_agent_type`.

If the first goal is `goal_choose_agent_type` the agent will support multiple goals using goal categories defined by `GOAL_CATEGORIES` in your .env file. If unset, default is all. We recommend starting with `fin`.
```bash
GOAL_CATEGORIES=hr,travel-flights,travel-trains,fin
```

See the section Goal-Specific Tool Configuration below for tool configuration for specific goals.

### LLM Configuration

Note: We recommend using OpenAI's GPT-4o or Claude 3.5 Sonnet for the best results. There can be significant differences in performance and capabilities between models, especially for complex tasks.

The agent uses LiteLLM to interact with various LLM providers. Configure the following environment variables in your `.env` file:

- `LLM_MODEL`: The model to use (e.g., "openai/gpt-4o", "anthropic/claude-3-sonnet", "google/gemini-pro", etc.)
- `LLM_KEY`: Your API key for the selected provider
- `LLM_BASE_URL`: (Optional) Custom base URL for the LLM provider. Useful for:
  - Using Ollama with a custom endpoint
  - Using a proxy or custom API gateway
  - Testing with different API versions

LiteLLM will automatically detect the provider based on the model name. For example:
- For OpenAI models: `openai/gpt-4o` or `openai/gpt-3.5-turbo`
- For Anthropic models: `anthropic/claude-3-sonnet`
- For Google models: `google/gemini-pro`
- For Ollama models: `ollama/mistral` (requires `LLM_BASE_URL` set to your Ollama server)

Example configurations:
```bash
# For OpenAI
LLM_MODEL=openai/gpt-4o
LLM_KEY=your-api-key-here

# For Anthropic
LLM_MODEL=anthropic/claude-3-sonnet
LLM_KEY=your-api-key-here

# For Ollama with custom URL
LLM_MODEL=ollama/mistral
LLM_BASE_URL=http://localhost:11434
```

For a complete list of supported models and providers, visit the [LiteLLM documentation](https://docs.litellm.ai/docs/providers).

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

You can also run a local Temporal server using Docker Compose. See the `Development with Docker` section below.

## Running the Application

### Docker
- All services are defined in `docker-compose.yml` (includes a Temporal server).
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

Default urls:
* Temporal UI: [http://localhost:8080](http://localhost:8080)
* API: [http://localhost:8000](http://localhost:8000)
* Frontend: [http://localhost:5173](http://localhost:5173)

### Local Machine (no docker)

**Python Backend**

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

**React UI**
Start the frontend:
```bash
cd frontend
npm install
npx vite
```
Access the UI at `http://localhost:5173`


## Goal-Specific Tool Configuration
Here is configuration guidance for specific goals. Travel and financial goals have configuration & setup as below.
### Goal: Find an event in Australia / New Zealand, book flights to it and invoice the user for the cost
- `AGENT_GOAL=goal_event_flight_invoice` - Helps users find events, book flights, and arrange train travel with invoice generation
    - This is the scenario in the [original video](https://www.youtube.com/watch?v=GEXllEH2XiQ)

#### Configuring Agent Goal: goal_event_flight_invoice
* The agent uses a mock function to search for events. This has zero configuration.
* By default the agent uses a mock function to search for flights.
    * If you want to use the real flights API, go to `tools/search_flights.py` and replace the `search_flights` function with `search_flights_real_api` that exists in the same file.
    * It's free to sign up at [RapidAPI](https://rapidapi.com/apiheya/api/sky-scrapper)
    * This api might be slow to respond, so you may want to increase the start to close timeout, `TOOL_ACTIVITY_START_TO_CLOSE_TIMEOUT` in `workflows/workflow_helpers.py`
* Requires a Stripe key for the `create_invoice` tool. Set this in the `STRIPE_API_KEY` environment variable in .env
    * It's free to sign up and get a key at [Stripe](https://stripe.com/)
        * Set permissions for read-write on: `Credit Notes, Invoices, Customers and Customer Sessions`
    * If you don't have a Stripe key, comment out the STRIPE_API_KEY in the .env file, and a dummy invoice will be created rather than a Stripe invoice. The function can be found in `tools/create_invoice.py`

### Goal: Find a Premier League match, book train tickets to it and invoice the user for the cost (Replay 2025 Keynote)
- `AGENT_GOAL=goal_match_train_invoice` - Focuses on Premier League match attendance with train booking and invoice generation
    - This goal was part of [Temporal's Replay 2025 conference keynote demo](https://www.youtube.com/watch?v=YDxAWrIBQNE)
    - Note, there is failure built in to this demo (the train booking step) to show how the agent can handle failures and retry. See Tool Configuration below for details.
#### Configuring Agent Goal: goal_match_train_invoice
NOTE: This goal was developed for an on-stage demo and has failure (and its resolution) built in to show how the agent can handle failures and retry.
* Omit `FOOTBALL_DATA_API_KEY` from .env for the `SearchFixtures` tool to automatically return mock Premier League fixtures. Finding a real match requires a key from [Football Data](https://www.football-data.org). Sign up for a free account, then see the 'My Account' page to get your API token.
* We use a mock function to search for trains. Start the train API server to use the real API: `python thirdparty/train_api.py`
* * The train activity is 'enterprise' so it's written in C# and requires a .NET runtime. See the [.NET backend](#net-(enterprise)-backend) section for details on running it.
* Requires a Stripe key for the `create_invoice` tool. Set this in the `STRIPE_API_KEY` environment variable in .env
    * It's free to sign up and get a key at [Stripe](https://stripe.com/)
    * If you're lazy go to `tools/create_invoice.py` and replace the `create_invoice` function with the mock `create_invoice_example` that exists in the same file.

##### Python Search Trains API
> Agent Goal: goal_match_train_invoice only

Required to search and book trains!
```bash
poetry run python thirdparty/train_api.py

# example url
# http://localhost:8080/api/search?from=london&to=liverpool&outbound_time=2025-04-18T09:00:00&inbound_time=2025-04-20T09:00:00
```

 ##### Python Train Legacy Worker
 > Agent Goal: goal_match_train_invoice only

 These are Python activities that fail (raise NotImplemented) to show how Temporal handles a failure. You can run these activities with.

 ```bash
 poetry run python scripts/run_legacy_worker.py
 ```

 The activity will fail and be retried infinitely. To rescue the activity (and its corresponding workflows), kill the worker and run the .NET one in the section below.

 ##### .NET (enterprise) Worker ;)
We have activities written in C# to call the train APIs.
```bash
cd enterprise
dotnet build # ensure you brew install dotnet@8 first!
dotnet run
```
If you're running your train API above on a different host/port then change the API URL in `Program.cs`. Otherwise, be sure to run it using `python thirdparty/train_api.py`.

#### Goals: FIN - Money Movement and Loan Application
Make sure you have the mock users you want (such as yourself) in [the account mock data file](./tools/data/customer_account_data.json).

- `AGENT_GOAL=goal_fin_move_money` - This scenario _can_ initiate a secondary workflow to move money. Check out [this repo](https://github.com/temporal-sa/temporal-money-transfer-java) - you'll need to get the worker running and connected to the same account as the agentic worker.
By default it will _not_ make a real workflow, it'll just fake it. If you get the worker running and want to start a workflow, in your [.env](./.env):
```bash
FIN_START_REAL_WORKFLOW=FALSE #set this to true to start a real workflow
```
- `AGENT_GOAL=goal_fin_loan_application` - This scenario _can_ initiate a secondary workflow to apply for a loan. Check out [this repo](https://github.com/temporal-sa/temporal-latency-optimization-scenarios) - you'll need to get the worker running and connected to the same account as the agentic worker.
By default it will _not_ make a real workflow, it'll just fake it. If you get the worker running and want to start a workflow, in your [.env](./.env):
```bash
FIN_START_REAL_WORKFLOW=FALSE #set this to true to start a real workflow
```

#### Goals: HR/PTO
Make sure you have the mock users you want in (such as yourself) in [the PTO mock data file](./tools/data/employee_pto_data.json).

#### Goals: Ecommerce
Make sure you have the mock orders you want in (such as those with real tracking numbers) in [the mock orders file](./tools/data/customer_order_data.json).


## Customizing the Agent Further
- `tool_registry.py` contains the mapping of tool names to tool definitions (so the AI understands how to use them)
- `goal_registry.py` contains descriptions of goals and the tools used to achieve them
- The tools themselves are defined in their own files in `/tools`
- Note the mapping in `tools/__init__.py` to each tool

For more details, check out [adding goals and tools guide](./adding-goals-and-tools.md).

## Setup Checklist
[  ] copy `.env.example` to `.env` <br />
[  ] Select an LLM and add your API key to `.env` <br />
[  ] (Optional) set your starting goal and goal category in  `.env` <br />
[  ] (Optional) configure your Temporal Cloud settings in  `.env` <br />
[  ] `poetry run python scripts/run_worker.py` <br />
[  ] `poetry run uvicorn api.main:app --reload` <br />
[  ] `cd frontend`, `npm install`, `npx vite` <br />
[ ] Access the UI at `http://localhost:5173` <br />

And that's it! Happy AI Agent Exploring!
