# ── Stage 1: Install dependencies ─────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build tools needed for scikit-surprise Cython extensions
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install production dependencies only (no dev deps)
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

# ── Stage 2: Production image ────────────────────────────────
FROM python:3.12-slim AS production

WORKDIR /app

# Create non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy uv and installed dependencies from builder
COPY --from=builder /bin/uv /bin/uvx /bin/
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/pyproject.toml /app/uv.lock* /app/

# Copy application code
COPY app/ app/

# Switch to non-root user
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Production server with 2 workers (suitable for demo/portfolio use)
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
