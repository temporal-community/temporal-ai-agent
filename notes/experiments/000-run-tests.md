# Experiment 000 - Run Tests
## Objective
- Run tests for the Temporal AI Agent project

## Steps
1. Install poetry if not already installed
`brew install poetry`
2. Install development dependencies
`poetry install --with dev`
2. Run the tests `poetry run pytest`

## Issues and fixes

### No module named pytest_asyncio
**Error**
```
ImportError while loading conftest '/Users/joeszodfridt/src/temporal/temporal-ai-agent/tests/conftest.py'.
tests/conftest.py:7: in <module>
    import pytest_asyncio
E   ModuleNotFoundError: No module named 'pytest_asyncio'
```
**Remediation**
- Install development dependencies
`poetry install --with dev`
