# Stage 1: Build
FROM python:3.11-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies for build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (Force clean rebuild - mysqlclient completely removed 2026-05-26)
COPY requirements/ /app/requirements/
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements/production.txt -r requirements/base.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN addgroup --system appgroup && adduser --system --group appuser

# Install wheels from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements /app/requirements
RUN pip install --no-cache /wheels/*

# Copy project files
COPY . /app/

# Make entrypoint.sh executable
RUN chmod +x /app/entrypoint.sh

# Set ownership
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
