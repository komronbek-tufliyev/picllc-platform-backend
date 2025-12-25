#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z ${DB_HOST:-postgres} ${DB_PORT:-5432}; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "Waiting for Redis..."
while ! nc -z redis ${REDIS_PORT:-6379}; do
  sleep 0.1
done
echo "Redis started"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Creating superuser if needed..."
if [ "${SKIP_SUPERUSER:-false}" = "true" ]; then
  echo "Skipping superuser creation (SKIP_SUPERUSER=true)"
else
python manage.py shell << EOF
from django.contrib.auth import get_user_model
import os
User = get_user_model()
admin_email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@ujmp.local')
admin_username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
admin_password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123')
if not User.objects.filter(email=admin_email).exists():
    # create_superuser expects username first, then email
    User.objects.create_superuser(admin_username, admin_email, admin_password)
    print(f'Superuser created: {admin_email} / {admin_password}')
else:
    print('Superuser already exists')
EOF
fi

echo "Starting application..."
exec "$@"
