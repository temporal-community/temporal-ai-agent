# Temporal AI Agent Contribution Guide

## Repository Layout
- `workflows/` - Temporal workflows including the main AgentGoalWorkflow for multi-turn AI conversations
- `activities/` - Temporal activities for tool execution and LLM interactions  
- `tools/` - AI agent tools organized by category (finance, HR, ecommerce, travel, etc.)
- `models/` - Data types and tool definitions used throughout the system
- `prompts/` - Agent prompt generators and templates
- `api/` - FastAPI server that exposes REST endpoints to interact with workflows
- `frontend/` - React-based web UI for chatting with the AI agent
- `tests/` - Comprehensive test suite for workflows and activities using Temporal's testing framework
- `enterprise/` - .NET worker implementation for enterprise activities (train booking)
- `scripts/` - Utility scripts for running workers and testing tools

## Running the Application

### Quick Start with Docker
```bash
# Start all services with development hot-reload
docker compose up -d

# Quick rebuild without infrastructure
docker compose up -d --no-deps --build api worker frontend
```

Default URLs:
- Temporal UI: http://localhost:8080
- API: http://localhost:8000  
- Frontend: http://localhost:5173

### Local Development Setup

1. **Prerequisites:**
   ```bash
   # Install Poetry for Python dependency management
   curl -sSL https://install.python-poetry.org | python3 -
   
   # Start Temporal server (Mac)
   brew install temporal
   temporal server start-dev
   ```

2. **Backend (Python):**
   ```bash
   # Quick setup using Makefile
   make setup              # Creates venv and installs dependencies
   make run-worker         # Starts the Temporal worker
   make run-api            # Starts the API server
   
   # Or manually:
   poetry install
   poetry run python scripts/run_worker.py    # In one terminal
   poetry run uvicorn api.main:app --reload   # In another terminal
   ```

3. **Frontend (React):**
   ```bash
   make run-frontend       # Using Makefile
   
   # Or manually:
   cd frontend
   npm install
   npx vite
   ```

4. **Enterprise .NET Worker (optional):**
   ```bash
   make run-enterprise     # Using Makefile
   
   # Or manually:
   cd enterprise
   dotnet build
   dotnet run
   ```

### Environment Configuration
Copy `.env.example` to `.env` and configure:
```bash
# Required: LLM Configuration
LLM_MODEL=openai/gpt-4o          # or anthropic/claude-3-sonnet, etc.
LLM_KEY=your-api-key-here

# Optional: Agent Goals and Categories  
AGENT_GOAL=goal_choose_agent_type
GOAL_CATEGORIES=hr,travel-flights,travel-trains,fin

# Optional: Tool-specific APIs
STRIPE_API_KEY=sk_test_...       # For invoice creation
FOOTBALL_DATA_API_KEY=...        # For real football fixtures
```

## Testing

The project includes comprehensive tests using Temporal's testing framework:

```bash
# Install test dependencies
poetry install --with dev

# Run all tests
poetry run pytest

# Run with time-skipping for faster execution  
poetry run pytest --workflow-environment=time-skipping

# Run specific test categories
poetry run pytest tests/test_tool_activities.py -v     # Activity tests
poetry run pytest tests/test_agent_goal_workflow.py -v # Workflow tests

# Run with coverage
poetry run pytest --cov=workflows --cov=activities
```

**Test Coverage:**
- ✅ **Workflow Tests**: AgentGoalWorkflow signals, queries, state management
- ✅ **Activity Tests**: ToolActivities, LLM integration (mocked), environment configuration  
- ✅ **Integration Tests**: End-to-end workflow and activity execution

**Documentation:**
- **Quick Start**: [TESTING.md](TESTING.md) - Simple commands to run tests
- **Comprehensive Guide**: [tests/README.md](tests/README.md) - Detailed testing patterns and best practices

## Linting and Code Quality

```bash
# Using Poetry tasks
poetry run poe format    # Format code with black and isort
poetry run poe lint      # Check code style and types
poetry run poe test      # Run test suite

# Manual commands  
poetry run black .
poetry run isort .
poetry run mypy --check-untyped-defs --namespace-packages .
```

## Agent Customization

### Adding New Tools
1. Create tool implementation in `tools/` directory
2. Add tool function mapping in `tools/__init__.py`  
3. Register tool definition in `tools/tool_registry.py`
4. Associate with goals in `tools/goal_registry.py`

### Configuring Goals
The agent supports multiple goal categories:
- **Financial**: Money transfers, loan applications (`fin/`)
- **HR**: PTO booking, payroll status (`hr/`)  
- **Travel**: Flight/train booking, event finding
- **Ecommerce**: Order tracking, package management (`ecommerce/`)

See [adding-goals-and-tools.md](adding-goals-and-tools.md) for detailed customization guide.

## Architecture

This system implements "Agentic AI" with these key components:
1. **Goals** - High-level objectives accomplished through tool sequences
2. **Agent Loops** - LLM execution → tool calls → human input → repeat until goal completion
3. **Tool Approval** - Human confirmation for sensitive operations
4. **Conversation Management** - LLM-powered input validation and history summarization
5. **Durability** - Temporal workflows ensure reliable execution across failures

For detailed architecture information, see [architecture.md](architecture.md).

## Commit Messages and Pull Requests
- Use clear commit messages describing the change purpose
- Reference specific files and line numbers when relevant (e.g., `workflows/agent_goal_workflow.py:125`)
- Open PRs describing **what changed** and **why**
- Ensure tests pass before submitting: `poetry run pytest --workflow-environment=time-skipping`

## Additional Resources
- **Setup Guide**: [SETUP.md](SETUP.md) - Detailed configuration instructions
- **Architecture Decisions**: [architecture-decisions.md](architecture-decisions.md) - Why Temporal for AI agents
- **Demo Video**: [5-minute YouTube overview](https://www.youtube.com/watch?v=GEXllEH2XiQ)
- **Multi-Agent Demo**: [Advanced multi-agent execution](https://www.youtube.com/watch?v=8Dc_0dC14yY)