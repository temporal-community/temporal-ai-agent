FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="$PATH:/root/.local/bin"

# Copy dependency files and README (needed for package build)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies and create virtual environment
RUN uv sync --frozen

# Copy application code
COPY . .

# Set Python to run in unbuffered mode (recommended for Docker)
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose the port the app will run on
EXPOSE 8000

# Default to running only the API server; worker and train-api are separate Compose services
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
