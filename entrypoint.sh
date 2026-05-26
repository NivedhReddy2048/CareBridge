#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL started."

echo "Waiting for Redis..."
while ! nc -z $REDIS_HOST $REDIS_PORT; do
  sleep 0.1
done
echo "Redis started."

# Ensure we're using production settings if in prod
if [ "$DJANGO_ENV" = "production" ]; then
    export DJANGO_SETTINGS_MODULE=config.settings.production
else
    export DJANGO_SETTINGS_MODULE=config.settings.local
fi

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
exec "$@"
