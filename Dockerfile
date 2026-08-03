# Disha Backend API - Production Dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PORT=8000

WORKDIR /app

# Install system dependencies & curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser binaries and OS system dependencies
RUN python -m playwright install --with-deps chromium

# Copy application source code
COPY main.py schemas.py ./
COPY agents/ ./agents/
COPY api/ ./api/
COPY tools/ ./tools/
COPY storage/ ./storage/
COPY profiles/ ./profiles/

# Create data directory for user memory storage
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Entrypoint command
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
