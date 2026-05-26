#!/bin/sh
set -e

echo "Starting CareBridge container..."

# Safe database URL parsing
if [ -z "$DB_HOST" ] && [ -n "$DATABASE_URL" ]; then
  clean_db_url="${DATABASE_URL#*://}"
  clean_db_url="${clean_db_url##*@}"
  DB_HOST="${clean_db_url%%:*}"
  temp_db_port="${clean_db_url#*:}"
  DB_PORT="${temp_db_port%%/*}"
fi

# Safe Redis URL parsing
if [ -z "$REDIS_HOST" ] && [ -n "$REDIS_URL" ]; then
  clean_url="${REDIS_URL#redis://}"
  clean_url="${clean_url##*@}"
  REDIS_HOST="${clean_url%%:*}"
  temp_port="${clean_url#*:}"
  REDIS_PORT="${temp_port%%/*}"
fi

# PostgreSQL wait logic
if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
  echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
  while ! nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 0.1
  done
  echo "PostgreSQL started."
else
  echo "DB_HOST or DB_PORT not set, skipping PostgreSQL wait."
fi

# Redis wait logic
if [ -n "$REDIS_HOST" ] && [ -n "$REDIS_PORT" ]; then
  echo "Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
  while ! nc -z "$REDIS_HOST" "$REDIS_PORT"; do
    sleep 0.1
  done
  echo "Redis started."
else
  echo "REDIS_HOST or REDIS_PORT not set, skipping Redis wait."
fi

# Ensure we're using production settings if in prod
if [ "$DJANGO_ENV" = "production" ]; then
    export DJANGO_SETTINGS_MODULE=config.settings.production
else
    export DJANGO_SETTINGS_MODULE=config.settings.local
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Checking superuser bootstrap..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
import os

User = get_user_model()

username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

try:
    if username and email and password:
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            print("Superuser created successfully.")
        else:
            print("Superuser already exists.")
    else:
        print("Superuser environment variables missing. Skipping bootstrap.")
except Exception as e:
    print(f"Superuser bootstrap skipped safely: {str(e)}")
EOF

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Daphne server..."
exec "$@"
