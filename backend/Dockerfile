# ---------- Build stage ----------
FROM python:3.12-slim AS builder

# Set up environment variables
ENV HOME=/home/appuser
ENV PATH="$HOME/.local/bin:$PATH"

# Install build dependencies
RUN apt-get update -qqy \
    && apt-get install -qqy --no-install-recommends \
    curl \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv globally
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir uv

# Create non-root user
RUN mkdir -p $HOME \
    && groupadd -g 1000 appuser \
    && useradd -r -u 1000 -g appuser appuser \
    && chown -R appuser $HOME

USER appuser
WORKDIR $HOME

# Copy dependency files
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# Install dependencies into a local .venv
RUN uv sync --frozen --no-dev --no-editable || \
    (mkdir -p src && uv sync --frozen --no-dev)

# ---------- Runtime stage ----------
FROM python:3.12-slim AS runtime

# Set up environment variables
ENV HOME=/home/appuser
ENV PATH="$HOME/.local/bin:$PATH"
ENV PYTHONPATH=/home/appuser/src
ARG PORT=8085
ENV HOST=0.0.0.0
ENV PORT=${PORT}

# Install runtime system dependencies only (lighter than builder)
RUN apt-get update -qqy \
    && apt-get install -qqy --no-install-recommends \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN mkdir -p $HOME \
    && groupadd -g 1000 appuser \
    && useradd -r -u 1000 -g appuser appuser \
    && chown -R appuser $HOME

USER appuser
WORKDIR $HOME

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appuser $HOME/.venv $HOME/.venv

# Ensure venv is used by default
ENV VIRTUAL_ENV=$HOME/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser asgi.py entrypoint.sh alembic.ini ./

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Health check (optional)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost:$PORT/health || exit 1

# Entrypoint
ENTRYPOINT ["./entrypoint.sh"]
CMD ["serve"]
EXPOSE ${PORT}
