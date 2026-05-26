# CareBridge Enterprise - Docker Development Guide

This guide explains how to build, run, and manage the CareBridge Enterprise AI Platform using Docker. The Dockerized environment ensures parity between local development and production deployments.

## Prerequisites
- Docker Engine installed (v20+)
- Docker Compose installed (v2+)

## Quick Start (Development)

To spin up the full stack (PostgreSQL, Redis, Celery, and Daphne ASGI Server) locally:

```bash
# Build the images and start the containers in detached mode
docker-compose up --build -d

# Check the status of the containers
docker-compose ps

# View logs for all services
docker-compose logs -f
```

The application will be accessible at `http://localhost:8000`.

## Available Services

The `docker-compose.yml` provisions the following services:
1. **web**: The main ASGI web application served by Daphne (Port 8000).
2. **db**: PostgreSQL 15 database (Port 5432).
3. **redis**: Redis cache and Celery broker (Port 6379).
4. **celery**: Celery worker for async tasks (e.g., Malware scanning, notifications).

## Important Commands

### Running Django Management Commands

You can run Django management commands inside the `web` container using `docker-compose exec`:

```bash
# Apply database migrations
docker-compose exec web python manage.py migrate

# Create a superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Run the test suite
docker-compose exec web python -m pytest
```

### Viewing Service-Specific Logs

To debug a specific service (like the Celery worker or Redis):

```bash
docker-compose logs -f celery
docker-compose logs -f db
docker-compose logs -f web
```

### Stopping and Tearing Down

To stop the containers without destroying data (volumes are preserved):

```bash
docker-compose stop
```

To bring down the entire stack and remove containers and networks (Warning: Use `-v` to also remove volumes if you want a fresh database):

```bash
docker-compose down
```

## Production Deployment

This project uses a `render.yaml` Blueprint for production deployment. When deploying to production environments like Render:
- The `Dockerfile` uses a multi-stage production build.
- Gunicorn+Daphne is used as the process supervisor.
- Environment variables (like `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `AWS_ACCESS_KEY_ID`) must be injected into the production environment.
- The `entrypoint.sh` script handles automated pre-start tasks like DB migrations and static file collection.

## Environment Variables

The `web` service relies on the `.env` file (which can be derived from `.env.example`). When running `docker-compose up`, ensure you have a valid `.env` file containing:

```env
# Required for AI Features
GEMINI_API_KEY=your_gemini_api_key

# Database and Cache (Overridden by docker-compose)
DATABASE_URL=postgres://carebridge_user:carebridge_pass@db:5432/carebridge_db
REDIS_URL=redis://redis:6379/1

# S3 Configuration (Optional for local development)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
```

## Health Monitoring
The platform exposes two internal health routes:
- **API Status:** `/api/v1/health/` (JSON structure monitoring DB, Celery, Storage)
- **Enterprise Dashboard:** `/enterprise/system-monitoring/` (Real-time HTML view with psutil metrics)
