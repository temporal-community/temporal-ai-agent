temporal: temporal server start-dev
worker:  source venv/bin/activate && poetry run python scripts/run_worker.py
api: source venv/bin/activate && poetry run uvicorn api.main:app --reload
ui: cd frontend && npx vite
