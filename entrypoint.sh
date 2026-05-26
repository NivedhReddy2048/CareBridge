#!/bin/sh
set -e

echo "Starting CareBridge container..."

# Ensure we're using production settings if in prod
if [ "$DJANGO_ENV" = "production" ]; then
    export DJANGO_SETTINGS_MODULE=config.settings.production
else
    export DJANGO_SETTINGS_MODULE=config.settings.local
fi

echo "Running migrations with retry-safe wrapper..."
max_attempts=10
attempt=1
success=0

while [ $attempt -le $max_attempts ]; do
    echo "Migration attempt $attempt of $max_attempts..."
    if python manage.py migrate --noinput; then
        echo "Migrations completed successfully!"
        success=1
        break
    else
        echo "Migration attempt $attempt failed. Retrying in 5 seconds..."
        sleep 5
        attempt=$((attempt + 1))
    fi
done

if [ $success -ne 1 ]; then
    echo "Error: Migrations failed after $max_attempts attempts. Exiting cleanly."
    exit 1
fi

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

# Render/Celery environment branching:
if [ "$1" = "celery" ] || [ "$1" = "python" ] || [ "$1" = "sh" ] || [ "$1" = "bash" ]; then
    echo "Running custom command: $@"
    exec "$@"
fi

echo "Starting Daphne web server..."
exec daphne -b 0.0.0.0 -p "$PORT" config.asgi:application
