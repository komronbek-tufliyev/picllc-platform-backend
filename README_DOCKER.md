# Docker Infrastructure - Quick Start

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Quick Start

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Generate secret key and update `.env`:**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

3. **Build and start all services:**
   ```bash
   docker-compose up -d --build
   ```

4. **Wait for services to be healthy (30-60 seconds)**

5. **Access the application:**
   - API: http://localhost/api/
   - Admin: http://localhost/admin/ (admin@ujmp.local / admin123)
   - API Docs: http://localhost/api/docs/
   - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
   - MailHog: http://localhost:8025
   - Flower: http://localhost:5555 (if enabled with `--profile monitoring`)

## Services Included

- **web** - Django application (Gunicorn)
- **postgres** - PostgreSQL database
- **redis** - Redis for Celery
- **celery_worker** - Celery worker process
- **celery_beat** - Celery scheduler
- **nginx** - Reverse proxy
- **minio** - S3-compatible storage
- **mailhog** - Email testing
- **flower** - Celery monitoring (optional)

## Common Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Run tests
docker-compose exec web python manage.py test
```

## Full Documentation

See `DOCKER.md` for complete documentation.

