# Temporal AI Agent - Testing Guide

This directory contains comprehensive tests for the Temporal AI Agent project. The tests cover workflows, activities, and integration scenarios using Temporal's testing framework.

## Table of Contents

- [Test Structure](#test-structure)
- [Test Types](#test-types)
  - [1. Workflow Tests (`test_agent_goal_workflow.py`)](#1-workflow-tests-test_agent_goal_workflowpy)
  - [2. Activity Tests (`test_tool_activities.py`)](#2-activity-tests-test_tool_activitiespy)
  - [3. Configuration Tests (`conftest.py`)](#3-configuration-tests-conftestpy)
- [Running Tests](#running-tests)
  - [Prerequisites](#prerequisites)
  - [Basic Test Execution](#basic-test-execution)
  - [Test Environment Options](#test-environment-options)
  - [Filtering Tests](#filtering-tests)
- [Test Configuration](#test-configuration)
  - [Test Discovery](#test-discovery)
  - [Environment Variables](#environment-variables)
  - [Mocking Strategy](#mocking-strategy)
- [Writing New Tests](#writing-new-tests)
  - [Test Naming Convention](#test-naming-convention)
  - [Using Fixtures](#using-fixtures)
  - [Mocking External Dependencies](#mocking-external-dependencies)
  - [Testing Workflow Signals and Queries](#testing-workflow-signals-and-queries)
- [Test Data and Fixtures](#test-data-and-fixtures)
  - [Sample Agent Goal](#sample-agent-goal)
  - [Sample Conversation History](#sample-conversation-history)
  - [Sample Combined Input](#sample-combined-input)
- [Debugging Tests](#debugging-tests)
  - [Verbose Logging](#verbose-logging)
  - [Temporal Web UI](#temporal-web-ui)
  - [Test Isolation](#test-isolation)
- [Continuous Integration](#continuous-integration)
  - [GitHub Actions Example](#github-actions-example)
  - [Test Coverage](#test-coverage)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
  - [Common Issues](#common-issues)
  - [Getting Help](#getting-help)
- [Legacy Tests](#legacy-tests)

## Test Structure

```
tests/
├── README.md                      # This file - testing documentation
├── conftest.py                    # Test configuration and fixtures
├── test_agent_goal_workflow.py    # Workflow tests
├── test_tool_activities.py        # Activity tests
└── workflowtests/                 # Legacy workflow tests
    └── agent_goal_workflow_test.py
```

## Test Types

### 1. Workflow Tests (`test_agent_goal_workflow.py`)

Tests the main `AgentGoalWorkflow` class covering:

- **Workflow Initialization**: Basic workflow startup and state management
- **Signal Handling**: Testing user_prompt, confirm, end_chat signals
- **Query Methods**: Testing all workflow query endpoints
- **State Management**: Conversation history, goal changes, tool data
- **Validation Flow**: Prompt validation and error handling
- **Tool Execution Flow**: Confirmation and tool execution cycles

### 2. Activity Tests (`test_tool_activities.py`)

Tests the `ToolActivities` class and `dynamic_tool_activity` function:

- **LLM Integration**: Testing agent_toolPlanner with mocked LLM responses
- **Validation Logic**: Testing agent_validatePrompt with various scenarios
- **Environment Configuration**: Testing get_wf_env_vars with different env setups
- **JSON Processing**: Testing response parsing and sanitization
- **Dynamic Tool Execution**: Testing the dynamic activity dispatcher
- **Integration**: End-to-end activity execution in Temporal workers

### 3. Configuration Tests (`conftest.py`)

Provides shared test fixtures and configuration:

- **Temporal Environment**: Local and time-skipping test environments
- **Sample Data**: Pre-configured agent goals, conversation history, inputs
- **Test Client**: Configured Temporal client for testing

## Running Tests

### Prerequisites

Ensure you have the required dependencies installed:

```bash
uv sync
```

### Basic Test Execution

Run all tests:
```bash
uv run pytest
```

Run specific test files:
```bash
# Workflow tests only
uv run pytest tests/test_agent_goal_workflow.py

# Activity tests only
uv run pytest tests/test_tool_activities.py

# Legacy tests
uv run pytest tests/workflowtests/
```

Run with verbose output:
```bash
uv run pytest -v
```

### Test Environment Options

The tests support different Temporal environments via the `--workflow-environment` flag:

#### Local Environment (Default)
Uses a local Temporal test server:
```bash
uv run pytest --workflow-environment=local
```

#### Time-Skipping Environment
Uses Temporal's time-skipping test environment for faster execution:
```bash
uv run pytest --workflow-environment=time-skipping
```

#### External Server
Connect to an existing Temporal server:
```bash
uv run pytest --workflow-environment=localhost:7233
```

#### Setup Script for AI Agent environments such as OpenAI Codex
```bash
export SHELL=/bin/bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
ls
uv sync
cd frontend
npm install
cd ..

# Pre-download the temporal test server binary
uv run python -c "
import asyncio
import sys
from temporalio.testing import WorkflowEnvironment

async def predownload():
    try:
        print('Starting test server download...')
        env = await WorkflowEnvironment.start_time_skipping()
        print('Test server downloaded and started successfully')
        await env.shutdown()
        print('Test server shut down successfully')
    except Exception as e:
        print(f'Error during download: {e}')
        sys.exit(1)

asyncio.run(predownload())
"
```

### Filtering Tests

Run tests by pattern:
```bash
# Run only validation tests
uv run pytest -k "validation"

# Run only workflow tests
uv run pytest -k "workflow"

# Run only activity tests
uv run pytest -k "activity"
```

Run tests by marker (if you add custom markers):
```bash
# Run only integration tests
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not slow"
```

## Test Configuration

### Test Discovery

The `vibe/` directory is excluded from test collection to avoid conflicts with sample tests. This is configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
norecursedirs = ["vibe"]
```

### Environment Variables

Tests respect the following environment variables:

- `LLM_MODEL`: Model to use for LLM testing (defaults to "openai/gpt-4")
- `LLM_KEY`: API key for LLM service
- `LLM_BASE_URL`: Custom base URL for LLM service
- `SHOW_CONFIRM`: Whether to show confirmation dialogs
- `AGENT_GOAL`: Default agent goal setting

### Mocking Strategy

The tests use extensive mocking to avoid external dependencies:

- **LLM Calls**: Mocked using `unittest.mock` to avoid actual API calls
- **Tool Handlers**: Mocked to test workflow logic without tool execution
- **Environment Variables**: Patched for consistent test environments

## Writing New Tests

### Test Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<functionality>_<scenario>`

Example:
```python
class TestAgentGoalWorkflow:
    async def test_user_prompt_signal_valid_input(self, client, sample_combined_input):
        # Test implementation
        pass
```

### Using Fixtures

Leverage the provided fixtures for consistent test data:

```python
async def test_my_workflow(self, client, sample_agent_goal, sample_conversation_history):
    # client: Temporal test client
    # sample_agent_goal: Pre-configured AgentGoal
    # sample_conversation_history: Sample conversation data
    pass
```

### Mocking External Dependencies

Always mock external services:

```python
@patch('activities.tool_activities.completion')
async def test_llm_integration(self, mock_completion):
    mock_completion.return_value.choices[0].message.content = '{"test": "response"}'
    # Test implementation
```

### Testing Workflow Signals and Queries

```python
async def test_workflow_signal(self, client, sample_combined_input):
    # Start workflow
    handle = await client.start_workflow(
        AgentGoalWorkflow.run,
        sample_combined_input,
        id=str(uuid.uuid4()),
        task_queue=task_queue_name,
    )
    
    # Send signal
    await handle.signal(AgentGoalWorkflow.user_prompt, "test message")
    
    # Query state
    conversation = await handle.query(AgentGoalWorkflow.get_conversation_history)
    
    # End workflow
    await handle.signal(AgentGoalWorkflow.end_chat)
    result = await handle.result()
```

## Test Data and Fixtures

### Sample Agent Goal

The `sample_agent_goal` fixture provides a basic agent goal with:
- Goal ID: "test_goal"
- One test tool with a required string argument
- Suitable for most workflow testing scenarios

### Sample Conversation History

The `sample_conversation_history` fixture provides:
- Basic user and agent message exchange
- Proper message format for testing

### Sample Combined Input

The `sample_combined_input` fixture provides:
- Complete workflow input with agent goal and tool params
- Conversation summary and prompt queue
- Ready for workflow execution

## Debugging Tests

### Verbose Logging

Enable detailed logging:
```bash
uv run pytest --log-cli-level=DEBUG -s
```

### Temporal Web UI

When using local environment, access Temporal Web UI at http://localhost:8233 to inspect workflow executions during tests.

### Test Isolation

Each test uses unique task queue names to prevent interference:
```python
task_queue_name = str(uuid.uuid4())
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync
      - run: uv run pytest --workflow-environment=time-skipping
```

### Test Coverage

Generate coverage reports:
```bash
uv add --group dev pytest-cov
uv run pytest --cov=workflows --cov=activities --cov-report=html
```

## Best Practices

1. **Mock External Dependencies**: Always mock LLM calls, file I/O, and network requests
2. **Use Time-Skipping**: For CI/CD, prefer time-skipping environment for speed
3. **Unique Identifiers**: Use UUIDs for workflow IDs and task queues
4. **Clean Shutdown**: Always end workflows properly in tests
5. **Descriptive Names**: Use clear, descriptive test names
6. **Test Edge Cases**: Include error scenarios and validation failures
7. **Keep Tests Fast**: Use mocks to avoid slow external calls
8. **Isolate Tests**: Ensure tests don't depend on each other

## Troubleshooting

### Common Issues

1. **Workflow Timeout**: Increase timeouts or use time-skipping environment
2. **Mock Not Working**: Check patch decorators and import paths
3. **Test Hanging**: Ensure workflows are properly ended with signals
4. **Environment Issues**: Check environment variable settings

### Getting Help

- Check Temporal Python SDK documentation
- Review existing test patterns in the codebase
- Use `uv run pytest --collect-only` to verify test discovery
- Run with `-v` flag for detailed output

## Legacy Tests

The `workflowtests/` directory contains legacy tests. New tests should be added to the main `tests/` directory following the patterns established in this guide.