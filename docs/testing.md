# Testing the Temporal AI Agent

This guide provides instructions for running the comprehensive test suite for the Temporal AI Agent project.

## Quick Start

1. **Install dependencies**:
   ```bash
   poetry install --with dev
   ```

2. **Run all tests**:
   ```bash
   poetry run pytest
   ```

3. **Run with time-skipping for faster execution**:
   ```bash
   poetry run pytest --workflow-environment=time-skipping
   ```

## Test Categories

### Unit Tests
- **Activity Tests**: `tests/test_tool_activities.py`
  - LLM integration (mocked)
  - Environment configuration
  - JSON processing
  - Dynamic tool execution

### Integration Tests  
- **Workflow Tests**: `tests/test_agent_goal_workflow.py`
  - Full workflow execution
  - Signal and query handling
  - State management
  - Error scenarios

## Running Specific Tests

```bash
# Run only activity tests
poetry run pytest tests/test_tool_activities.py -v

# Run only workflow tests  
poetry run pytest tests/test_agent_goal_workflow.py -v

# Run a specific test
poetry run pytest tests/test_tool_activities.py::TestToolActivities::test_sanitize_json_response -v

# Run tests matching a pattern
poetry run pytest -k "validation" -v
```

## Test Environment Options

### Local Environment (Default)
```bash
poetry run pytest --workflow-environment=local
```

### Time-Skipping Environment (Recommended for CI)
```bash
poetry run pytest --workflow-environment=time-skipping
```

### External Temporal Server
```bash
poetry run pytest --workflow-environment=localhost:7233
```

## Environment Variables

Tests can be configured with these environment variables:

- `LLM_MODEL`: Model for LLM testing (default: "openai/gpt-4")
- `LLM_KEY`: API key for LLM service (mocked in tests)
- `LLM_BASE_URL`: Custom LLM endpoint (optional)

## Test Coverage

The test suite covers:

✅ **Workflows**
- AgentGoalWorkflow initialization and execution
- Signal handling (user_prompt, confirm, end_chat)
- Query methods (conversation history, agent goal, tool data)
- State management and conversation flow
- Validation and error handling

✅ **Activities**  
- ToolActivities class methods
- LLM integration (mocked)
- Environment variable handling
- JSON response processing
- Dynamic tool activity execution

✅ **Integration**
- End-to-end workflow execution
- Activity registration in workers
- Temporal client interactions

## Test Output

Successful test run example:
```
============================== test session starts ==============================
platform darwin -- Python 3.11.3, pytest-8.3.5, pluggy-1.5.0
rootdir: /Users/steveandroulakis/Documents/Code/agentic/temporal-demo/temporal-ai-agent
configfile: pyproject.toml
plugins: anyio-4.5.2, asyncio-0.26.0
collected 21 items

tests/test_tool_activities.py::TestToolActivities::test_sanitize_json_response PASSED
tests/test_tool_activities.py::TestToolActivities::test_parse_json_response_success PASSED
tests/test_tool_activities.py::TestToolActivities::test_get_wf_env_vars_default_values PASSED
...

============================== 21 passed in 12.5s ==============================
```

## Troubleshooting

### Common Issues

1. **Module not found errors**: Run `poetry install --with dev`
2. **Async warnings**: These are expected with pytest-asyncio and can be ignored  
3. **Test timeouts**: Use `--workflow-environment=time-skipping` for faster execution
4. **Import errors**: Check that you're running tests from the project root directory

### Debugging Tests

Enable verbose logging:
```bash
poetry run pytest --log-cli-level=DEBUG -s
```

Run with coverage:
```bash
poetry run pytest --cov=workflows --cov=activities
```

## Continuous Integration

For CI environments, use:
```bash
poetry run pytest --workflow-environment=time-skipping --tb=short
```

## Additional Resources

- See `tests/README.md` for detailed testing documentation
- Review `tests/conftest.py` for available test fixtures
- Check individual test files for specific test scenarios

## Test Architecture

The tests use:
- **Temporal Testing Framework**: For workflow and activity testing
- **pytest-asyncio**: For async test support  
- **unittest.mock**: For mocking external dependencies
- **Test Fixtures**: For consistent test data and setup

All external dependencies (LLM calls, file I/O) are mocked to ensure fast, reliable tests.