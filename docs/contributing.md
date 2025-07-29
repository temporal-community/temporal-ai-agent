# Contributing to the Temporal AI Agent Project

This document provides guidelines for contributing to `temporal-ai-agent`. All setup and installation instructions can be found in [setup.md](./setup.md).

## Getting Started

### Code Style & Formatting
We use `black` for code formatting and `isort` for import sorting to maintain a consistent codebase.
-   **Format code:**
    ```bash
    uv run poe format
    ```
    Or manually
    ```
    uv run black .
    uv run isort .
    ```
    Please format your code before committing.

### Linting & Type Checking
We use `mypy` for static type checking and other linters configured via `poe`.
-   **Run linters and type checks:**
    ```bash
    uv run poe lint
    ```
    Or manually for type checking:
    ```bash
    uv run mypy --check-untyped-defs --namespace-packages .
    ```
    Ensure all linting and type checks pass before submitting a pull request.

## Testing
Comprehensive testing is crucial for this project. We use `pytest` and Temporal's testing framework.
-   **Install test dependencies:**
    ```bash
    uv sync
    ```
-   **Run all tests:**
    ```bash
    uv run pytest
    ```
-   **Run tests with time-skipping (recommended for faster execution, especially in CI):**
    ```bash
    uv run pytest --workflow-environment=time-skipping
    ```

For detailed information on test categories, running specific tests, test environments, coverage, and troubleshooting, please refer to:
-   [testing.md](./testing.md) (Quick Start and overview)
-   [tests/README.md](../tests/README.md) (Comprehensive guide, patterns, and best practices)

**Ensure all tests pass before submitting a pull request.**

## Making Changes

### Adding New Tools or Goals
If you're looking to extend the agent's capabilities:
1.  Create your tool implementation in the `tools/` directory.
2.  Register your tool and associate it with relevant goals.
For detailed instructions, please see:
-   [Agent Customization in AGENTS.md](../AGENTS.md#agent-customization)
-   [Adding Goals and Tools Guide](./adding-goals-and-tools.md)

### General Code Changes
-   Follow the existing code style and patterns.
-   Ensure any new code is well-documented with comments.
-   Write new tests for new functionality or bug fixes.
-   Update existing tests if necessary.

## Submitting Contributions

### Pull Requests
When you're ready to submit your changes:
1.  Push your branch to the remote repository.
2.  Open a Pull Request (PR) against the `main` branch.
3.  **Describe your changes:** Clearly explain what you changed and why. Reference any related issues.
4.  **Ensure tests pass:** All CI checks, including tests and linters, must pass. The command `uv run pytest --workflow-environment=time-skipping` is a good one to run locally.
5.  **Request review:** Request a review from one or more maintainers.

## Reporting Bugs
If you encounter a bug, please:
1.  **Search existing issues:** Check if the bug has already been reported.
2.  **Open a new issue:** If not, create a new issue.
    -   Provide a clear and descriptive title.
    -   Include steps to reproduce the bug.
    -   Describe the expected behavior and what actually happened.
    -   Provide details about your environment (OS, Python version, Temporal server version, etc.).
    -   Include any relevant logs or screenshots.

## Suggesting Enhancements
We welcome suggestions for new features or improvements!
1.  **Search existing issues/discussions:** See if your idea has already been discussed.
2.  **Open a new issue:**
    -   Use a clear and descriptive title.
    -   Provide a detailed explanation of the enhancement and its benefits.
    -   Explain the use case or problem it solves.
    -   Include any potential implementation ideas if you have them.

## Key Resources
-   **Project Overview**: [README.md](../README.md)
-   **Detailed Contribution & Development Guide**: [AGENTS.md](../AGENTS.md)
-   **Setup Instructions**: [setup.md](./setup.md)
-   **Comprehensive Testing Guide**: [testing.md](./testing.md) and [tests/README.md](../tests/README.md)
-   **System Architecture**: [architecture.md](./architecture.md)
-   **Architecture Decisions**: [architecture-decisions.md](./architecture-decisions.md)
-   **Customizing Agent Tools and Goals**: [adding-goals-and-tools.md](./adding-goals-and-tools.md)
-   **To-Do List / Future Enhancements**: [todo.md](./todo.md)