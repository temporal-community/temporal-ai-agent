.PHONY: setup install run-worker run-api run-frontend run-train-api run-legacy-worker run-enterprise setup-venv check-python

# Setup commands
setup: check-python setup-venv install

check-python:
	@which python3 >/dev/null 2>&1 || (echo "Python 3 is required. Please install it first." && exit 1)

setup-venv:
	python3 -m venv venv
	@echo "Virtual environment created. Don't forget to activate it with 'source venv/bin/activate'"

install:
	poetry install
	cd frontend && npm install

# Run commands
run-worker:
	poetry run python scripts/run_worker.py

run-api:
	poetry run uvicorn api.main:app --reload

run-frontend:
	cd frontend && npx vite

run-train-api:
	poetry run python thirdparty/train_api.py

run-legacy-worker:
	poetry run python scripts/run_legacy_worker.py

run-enterprise:
	cd enterprise && dotnet build && dotnet run

# Development environment setup
setup-temporal-mac:
	brew install temporal
	temporal server start-dev

# Help command
help:
	@echo "Available commands:"
	@echo "  make setup              - Create virtual environment and install dependencies"
	@echo "  make setup-venv         - Create virtual environment only"
	@echo "  make install            - Install all dependencies"
	@echo "  make run-worker         - Start the Temporal worker"
	@echo "  make run-api            - Start the API server"
	@echo "  make run-frontend       - Start the frontend development server"
	@echo "  make run-train-api      - Start the train API server"
	@echo "  make run-legacy-worker  - Start the legacy worker"
	@echo "  make run-enterprise     - Build and run the enterprise .NET worker"
	@echo "  make setup-temporal-mac - Install and start Temporal server on Mac" 