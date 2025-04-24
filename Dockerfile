FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
RUN pip install --no-cache-dir poetry

# Install Python dependencies without creating a virtualenv
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --without dev --no-interaction --no-ansi --no-root

# Copy application code
COPY . .

# Set Python to run in unbuffered mode (recommended for Docker)
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose the port the app will run on
EXPOSE 8000

# Default to running only the API server; worker and train-api are separate Compose services
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
