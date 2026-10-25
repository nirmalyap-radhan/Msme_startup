# Multi-stage production container for Udyog Sathi
FROM python:3.11-slim AS runtime

# System environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    PORT=8000

# Install system dependencies (OCR, Tesseract Odia & Hindi language packs, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-ori \
    tesseract-ocr-hin \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged application user
RUN useradd -u 1001 -m -s /bin/bash appuser

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and verified datasets
COPY --chown=appuser:appuser apps/ ./apps/
COPY --chown=appuser:appuser services/ ./services/
COPY --chown=appuser:appuser scripts/ ./scripts/
COPY --chown=appuser:appuser migrations/ ./migrations/
COPY --chown=appuser:appuser data/ ./data/
COPY --chown=appuser:appuser alembic.ini .

# Ensure data directory has correct permissions
RUN mkdir -p /app/data/backups && chown -R appuser:appuser /app/data

USER appuser

EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Start Uvicorn ASGI server with dynamic port support for cloud free tiers
CMD ["sh", "-c", "uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]

