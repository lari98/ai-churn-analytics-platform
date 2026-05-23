# ──────────────────────────────────────────────────────────────────────────────
# Multi-stage Production Dockerfile
# AI Churn Analytics Platform — FastAPI Backend
# Base: Python 3.11-slim | Non-root user | No secrets in image
# ──────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Dependency Builder ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install system dependencies for compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into /install (isolated from system)
COPY api/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Production Image ─────────────────────────────────────────────────
FROM python:3.11-slim AS production

LABEL maintainer="platform@churn-analytics.example.com"
LABEL version="1.0.0"
LABEL description="AI Churn Analytics Platform API"

# Security: non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup -u 1001 appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY api/ ./api/

# Create necessary directories with correct permissions
RUN mkdir -p /app/logs && \
    chown -R appuser:appgroup /app && \
    chmod -R 750 /app

# Security: no writable areas outside /app/logs
USER appuser

# Environment defaults (overridden by Azure Container Apps secrets)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    WORKERS=4 \
    LOG_LEVEL=info

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start with gunicorn + uvicorn workers
CMD ["sh", "-c", "gunicorn api.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers ${WORKERS} \
    --bind 0.0.0.0:${PORT} \
    --timeout 60 \
    --keepalive 5 \
    --access-logfile - \
    --error-logfile - \
    --log-level ${LOG_LEVEL}"]
