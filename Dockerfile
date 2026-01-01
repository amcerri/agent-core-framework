# Dockerfile for Agent Core Framework
# Provides a reproducible runtime environment for development and testing.
# This is an optional artifact - the framework works identically without Docker.

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy dependency files
COPY pyproject.toml ./

# Configure Poetry to not create virtual environment (we're in a container)
RUN poetry config virtualenvs.create false

# Install dependencies
# Use ARG to allow optional extras (e.g., langgraph) via build args
# Note: poetry.lock may not exist (it's in .gitignore), Poetry will resolve and install dependencies
ARG EXTRAS=""
RUN if [ -n "$EXTRAS" ]; then \
      poetry install --no-interaction --no-ansi --extras "$EXTRAS"; \
    else \
      poetry install --no-interaction --no-ansi; \
    fi

# Copy application code
COPY agent_core/ ./agent_core/
COPY examples/ ./examples/

# Create directory for mounted configuration
# Configuration must be mounted externally - never embedded in image
RUN mkdir -p /app/config

# Set environment variable for default config location
ENV AGENT_CORE_CONFIG=/app/config/agent-core.yaml

# Default command (can be overridden)
# Users should mount their config and run their own commands
CMD ["python", "-c", "from agent_core.runtime import Runtime; print('Agent Core Framework runtime ready')"]

