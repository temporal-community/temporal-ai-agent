.PHONY: setup install run-worker run-api run-frontend run-train-api run-legacy-worker run-enterprise setup-venv check-python run-dev

setup:
	uv sync
	cd frontend && npm install

# Run commands
run-worker:
	uv run scripts/run_worker.py

run-api:
	uv run uvicorn api.main:app --reload

run-frontend:
	cd frontend && npx vite

run-train-api:
	uv run thirdparty/train_api.py

run-legacy-worker:
	uv run scripts/run_legacy_worker.py

run-enterprise:
	cd enterprise && dotnet build && dotnet run

# Development environment setup
setup-temporal-mac:
	brew install temporal
	temporal server start-dev

# Run all development services
run-dev:
	@echo "Starting all development services..."
	@make run-worker & \
	make run-api & \
	make run-frontend & \
	wait

# Help command
help:
	@echo "Available commands:"
	@echo "  make setup              - Install all dependencies"
	@echo "  make run-worker         - Start the Temporal worker"
	@echo "  make run-api            - Start the API server"
	@echo "  make run-frontend       - Start the frontend development server"
	@echo "  make run-train-api      - Start the train API server"
	@echo "  make run-legacy-worker  - Start the legacy worker"
	@echo "  make run-enterprise     - Build and run the enterprise .NET worker"
	@echo "  make setup-temporal-mac - Install and start Temporal server on Mac"
	@echo "  make run-dev            - Start all development services (worker, API, frontend) in parallel"