# CareBridge Enterprise Deployment Guide

## Architecture Overview
CareBridge is a distributed asynchronous Django application. To safely deploy CareBridge in a production environment (like Render, AWS, or Heroku), you must provision three independent infrastructure layers:
1. **Web Workers (Daphne ASGI)**: Handles HTTP APIs, Django Admin, and WebRTC WebSocket signaling.
2. **Celery Workers**: Offloads Gemini AI Inference, EHR parsing, and async reporting.
3. **Data Stores**: PostgreSQL (Relational Database) and Redis (Pub/Sub & Celery Broker).

## Environment Variables
The application strictly reads from the environment. Ensure the following variables are securely injected into your deployment pipelines:

### Core Configuration
- `SECRET_KEY`: Minimum 60 characters. Do not use default.
- `DEBUG`: Must be exactly `False`.
- `ALLOWED_HOSTS`: Domain of your backend (e.g., `api.carebridge.com`).
- `RENDER_EXTERNAL_HOSTNAME`: Auto-injected if deploying to Render.

### Database & Caching
- `DATABASE_URL`: Standard PostgreSQL connection string.
- `REDIS_URL`: Redis URI used for Celery Broker, Result Backend, and Channels Layer.

### Third-Party APIs
- `GEMINI_API_KEY`: Google DeepMind Gemini Pro authorization token.
- `SENTRY_DSN`: Endpoint for Sentry error tracing.
- `AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY`: Required if storing EHR data remotely.
- `AWS_STORAGE_BUCKET_NAME`: Target S3 bucket for private media storage.

## Scaling Guidelines
- **WebSockets / Telemedicine**: Increase ASGI worker replicas dynamically. All WebSocket states are synchronized via the `REDIS_URL` `channels_redis` layer.
- **AI Orchestration**: If telemetry via `/enterprise/ai-workers/` shows rising backlog queues, independently scale your Celery worker pools.
- **Cache**: For high-traffic events, upgrade the Redis instance to support larger connection limits.
