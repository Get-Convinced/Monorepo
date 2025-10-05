# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy packages directory first for dependencies
COPY packages/database/ ./packages/database/

# Copy pyproject.toml and uv.lock first for better caching
COPY apps/backend/pyproject.toml apps/backend/uv.lock ./

# Install uv and dependencies (from monorepo root context)
RUN pip install uv && uv sync --no-dev

# Copy the source code
COPY apps/backend/src/ ./src/
COPY apps/backend/start_backend.py ./

# Set Python path to include packages
ENV PYTHONPATH="/app:/app/packages/database"

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Default command to start the backend using uv
CMD ["uv", "run", "python", "start_backend.py"]
