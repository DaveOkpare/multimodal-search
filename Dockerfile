# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12.1
FROM python:${PYTHON_VERSION}-slim AS base

# Prevents Python from writing pyc files and buffers stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set Streamlit environment variables
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_ENABLE_TELEMETRY=false

# Set default Qdrant connection variables
ENV QDRANT_HOST=localhost
ENV QDRANT_PORT=6333

WORKDIR /app

# Only install curl for healthcheck
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-privileged user with a proper home directory
ARG UID=10001
RUN mkdir -p /home/appuser && \
    adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/appuser" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser && \
    chown -R appuser:appuser /home/appuser

# Set environment variable for the cache directory
ENV HF_HOME=/home/appuser/huggingface
ENV TRANSFORMERS_CACHE=/home/appuser/huggingface
ENV XDG_CACHE_HOME=/home/appuser/cache

# Create and set permissions for cache directories
RUN mkdir -p /home/appuser/huggingface /home/appuser/cache && \
    chown -R appuser:appuser /home/appuser/huggingface /home/appuser/cache

# Copy the application files into the container
COPY --chown=appuser:appuser . .

# Install dependencies, avoiding cache to keep image small
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Switch to the non-privileged user
USER appuser

# Expose the Streamlit port
EXPOSE 8501

# Healthcheck with retries for better resilience
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit app
ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]