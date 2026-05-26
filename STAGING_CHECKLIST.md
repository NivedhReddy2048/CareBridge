# CareBridge Enterprise - Staging Deployment Checklist

This checklist ensures a reliable and structured deployment to the staging environment before moving to production.

## 1. Environment Validation
- [ ] Ensure `.env.staging` is populated and matches the `.env.example` schema.
- [ ] Verify `DEBUG=False` in staging.
- [ ] Verify `ALLOWED_HOSTS` includes the Render staging URL.
- [ ] Verify `CORS_ALLOWED_ORIGINS` is configured correctly.
- [ ] Validate `SECRET_KEY` is present and cryptographically secure.

## 2. Infrastructure Verification
- [ ] **Database:** Confirm the PostgreSQL instance is accessible (`psql -U ...`).
- [ ] **Redis:** Confirm Redis is available for caching and Celery (`redis-cli ping`).
- [ ] **Celery Workers:** Verify that the Celery worker process starts without errors.
- [ ] **AWS S3:** Ensure `AWS_ACCESS_KEY_ID` and `AWS_STORAGE_BUCKET_NAME` are configured. Confirm bucket permissions.
- [ ] **Sentry:** Verify `SENTRY_DSN` is set and staging events appear in the Sentry dashboard.

## 3. Migration Procedures
- [ ] Create a database backup before applying migrations (`./scripts/backup_db.sh`).
- [ ] Check for missing migrations: `python manage.py makemigrations --dry-run --check`.
- [ ] Run migrations safely: `python manage.py migrate`.
- [ ] Ensure no destructive schema changes (e.g., column drops without data migration) have been made without a rollback strategy.

## 4. Render Deployment Steps
- [ ] Trigger deployment in Render dashboard or via Git push.
- [ ] Monitor the Build logs for successful static file collection (`python manage.py collectstatic --noinput`).
- [ ] Monitor the Deploy logs for successful Daphne ASGI startup.
- [ ] Run Smoke Tests post-deployment: `python tests/smoke/smoke_runner.py`.

## 5. Subsystem Validation
- [ ] **WebSockets:** Verify real-time connections (e.g., notification stream) connect without 403 errors.
- [ ] **AI Engine:** Test the `/api/v1/ai/triage/` endpoint to ensure Gemini API integration functions correctly.
- [ ] **Static Files:** Load the Enterprise Dashboard and confirm CSS/JS assets return 200 OK via WhiteNoise.
- [ ] **Health Endpoint:** Hit `/api/v1/health/` and confirm a JSON payload returning `{"status": "healthy"}`.

## 6. Rollback Instructions
- **If App Fails:** Roll back the Render deployment to the previously successful commit via the Render dashboard.
- **If DB Corrupted:** Use `./scripts/restore_db.sh` to restore the timestamped SQL dump generated in Step 3.
- **Cache Invalidation:** Flush Redis cache (`redis-cli flushall`) to prevent stale schema references.
