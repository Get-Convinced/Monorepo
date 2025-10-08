# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory to match monorepo structure
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy packages directory first for dependencies
COPY packages/database/ ./packages/database/

# Copy backend app files
COPY apps/backend/pyproject.toml apps/backend/uv.lock ./apps/backend/
COPY apps/backend/src/ ./apps/backend/src/
COPY apps/backend/start_backend.py ./apps/backend/

# Change to backend directory for uv sync
WORKDIR /workspace/apps/backend

# Install uv and dependencies
RUN pip install uv && uv sync --no-dev

# Set Python path to include packages
ENV PYTHONPATH="/workspace:/workspace/packages/database"

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Default command to start the backend using uv
# Working directory is already /workspace/apps/backend
CMD ["uv", "run", "python", "start_backend.py"]
