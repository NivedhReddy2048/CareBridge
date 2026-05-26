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

echo "Starting server..."
exec "$@"
