#!/bin/bash
set -e

echo "Fixing permissions for volumes..."
# Only fix permissions if running as root (for gosu to work)
if [ "$(id -u)" = "0" ]; then
    # Create necessary media subdirectories
    mkdir -p /app/media/articles/manuscripts 2>/dev/null || true
    mkdir -p /app/media/certificates 2>/dev/null || true
    mkdir -p /app/media/invoices 2>/dev/null || true
    
    # Fix permissions on media directory, skipping system mount points
    if [ -d /app/media ]; then
        # Set ownership and permissions on the media directory itself
        chown -R ujmp:ujmp /app/media 2>/dev/null || true
        chmod -R 775 /app/media 2>/dev/null || true
        
        # Only chown/chmod actual directories, not system mount points
        for dir in /app/media/*; do
            if [ -d "$dir" ] && [ ! -L "$dir" ]; then
                case "$(basename "$dir")" in
                    floppy|usb|cdrom|proc|sys|dev)
                        # Skip system mount points
                        continue
                        ;;
                    *)
                        chown -R ujmp:ujmp "$dir" 2>/dev/null || true
                        chmod -R 775 "$dir" 2>/dev/null || true
                        ;;
                esac
            fi
        done
    fi
    # Fix permissions on staticfiles
    if [ -d /app/staticfiles ]; then
        chown -R ujmp:ujmp /app/staticfiles 2>/dev/null || true
        chmod -R 775 /app/staticfiles 2>/dev/null || true
    fi
fi

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

echo "Starting app as ujmp user..."
# If running as root, switch to ujmp user; otherwise run as current user
if [ "$(id -u)" = "0" ]; then
    exec gosu ujmp "$@"
else
    exec "$@"
fi