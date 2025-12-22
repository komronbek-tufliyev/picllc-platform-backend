# Docker Infrastructure Guide

**UJMP Backend - Docker Setup for Testing**

---

## Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

### Initial Setup

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Generate secret key:**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   Update `SECRET_KEY` in `.env`

3. **Build and start services:**
   ```bash
   docker-compose up -d --build
   ```

4. **Run migrations:**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. **Create superuser:**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. **Collect static files:**
   ```bash
   docker-compose exec web python manage.py collectstatic --noinput
   ```

### Access Services

- **API:** http://localhost/api/
- **API Docs:** http://localhost/api/docs/
- **Admin:** http://localhost/admin/
- **MinIO Console:** http://localhost:9001 (minioadmin/minioadmin)
- **MailHog:** http://localhost:8025
- **Flower:** http://localhost:5555 (if enabled)

---

## Services

### Web (Django)
- **Port:** 8000 (internal), 80 (via Nginx)
- **Command:** Gunicorn with 4 workers
- **Health Check:** `/health/`

### PostgreSQL
- **Port:** 5432
- **Database:** `ujmp` (configurable)
- **User:** `ujmp_user` (configurable)
- **Volume:** `postgres_data`

### Redis
- **Port:** 6379
- **Password:** `redis_password` (configurable)
- **Volume:** `redis_data`

### Celery Worker
- **Concurrency:** 4 workers
- **Log Level:** info
- **Depends on:** PostgreSQL, Redis, Web

### Celery Beat
- **Scheduler:** Celery beat
- **Log Level:** info
- **Depends on:** PostgreSQL, Redis

### Nginx
- **Ports:** 80, 443
- **Config:** `nginx/default.conf`
- **Static files:** `/static/`
- **Media files:** `/media/`

### MinIO
- **API Port:** 9000
- **Console Port:** 9001
- **Root User:** `minioadmin` (configurable)
- **Root Password:** `minioadmin` (configurable)
- **Volume:** `minio_data`

### MailHog
- **SMTP Port:** 1025
- **Web UI Port:** 8025
- **Purpose:** Email testing

### Flower (Optional)
- **Port:** 5555
- **Purpose:** Celery monitoring
- **Enable:** `docker-compose --profile monitoring up`

---

## Common Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery_worker
```

### Execute Commands
```bash
# Django shell
docker-compose exec web python manage.py shell

# Create migrations
docker-compose exec web python manage.py makemigrations

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Run tests
docker-compose exec web python manage.py test
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart web
docker-compose restart celery_worker
```

### Rebuild Services
```bash
# Rebuild all
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build web
```

---

## MinIO Setup

### Initial Configuration

1. **Access MinIO Console:**
   - URL: http://localhost:9001
   - Username: `minioadmin`
   - Password: `minioadmin`

2. **Create Bucket:**
   - Bucket name: `ujmp-media`
   - Set as public (for media files)

3. **Update Environment:**
   ```bash
   AWS_STORAGE_BUCKET_NAME=ujmp-media
   AWS_S3_ENDPOINT_URL=http://minio:9000
   ```

### Bucket Policy (Public Read)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::ujmp-media/*"
    }
  ]
}
```

---

## Development Mode

### Override Configuration

1. **Copy override example:**
   ```bash
   cp docker-compose.override.yml.example docker-compose.override.yml
   ```

2. **Customize for development:**
   - Use Django runserver instead of Gunicorn
   - Enable auto-reload for Celery
   - Mount volumes for live code changes

### Hot Reload

For development with hot reload:

```bash
# Use override file
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
```

---

## Testing

### Run Tests
```bash
docker-compose exec web python manage.py test --settings=ujmp.test_settings
```

### Test API Endpoints
```bash
# Health check
curl http://localhost/health/

# List journals
curl http://localhost/api/journals/

# With authentication
curl -H "Authorization: Bearer <token>" http://localhost/api/articles/
```

### Test Celery Tasks
```bash
# Check worker status
docker-compose exec celery_worker celery -A ujmp inspect active

# Monitor tasks (if Flower enabled)
# Access http://localhost:5555
```

### Test Email
```bash
# Send test email
docker-compose exec web python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Body', 'from@example.com', ['to@example.com'])

# Check MailHog: http://localhost:8025
```

---

## Troubleshooting

### Services Won't Start

**Check logs:**
```bash
docker-compose logs web
docker-compose logs postgres
docker-compose logs redis
```

**Common issues:**
- Port already in use
- Environment variables not set
- Database connection failed

### Database Connection Issues

**Test connection:**
```bash
docker-compose exec postgres psql -U ujmp_user -d ujmp -c "SELECT 1;"
```

**Reset database:**
```bash
docker-compose down -v
docker-compose up -d postgres
docker-compose exec web python manage.py migrate
```

### Celery Tasks Not Executing

**Check Redis:**
```bash
docker-compose exec redis redis-cli -a redis_password ping
```

**Check Celery:**
```bash
docker-compose exec celery_worker celery -A ujmp inspect active
```

**Restart Celery:**
```bash
docker-compose restart celery_worker celery_beat
```

### Static Files Not Loading

**Collect static files:**
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

**Check Nginx:**
```bash
docker-compose exec nginx ls -la /static/
```

### MinIO Connection Issues

**Test MinIO:**
```bash
curl http://localhost:9000/minio/health/live
```

**Check credentials:**
- Ensure `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` match MinIO root credentials
- Verify `AWS_S3_ENDPOINT_URL` is correct

---

## Data Persistence

### Volumes

- `postgres_data` - PostgreSQL data
- `redis_data` - Redis data
- `static_volume` - Static files
- `media_volume` - Media files
- `minio_data` - MinIO data

### Backup Database

```bash
docker-compose exec postgres pg_dump -U ujmp_user ujmp > backup.sql
```

### Restore Database

```bash
docker-compose exec -T postgres psql -U ujmp_user ujmp < backup.sql
```

### Clear All Data

```bash
# Stop and remove volumes
docker-compose down -v

# Rebuild
docker-compose up -d --build
```

---

## Production Considerations

**⚠️ This Docker setup is for testing/development only.**

For production:
- Use proper secrets management
- Configure SSL/TLS
- Set up proper backups
- Use production-grade database
- Configure proper logging
- Set up monitoring
- Use orchestration (Kubernetes, etc.)

---

## Environment Variables

See `.env.example` for all available environment variables.

Key variables:
- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (False in production)
- `DB_*` - Database configuration
- `CELERY_BROKER_URL` - Redis connection
- `AWS_*` - MinIO/S3 configuration
- `EMAIL_*` - MailHog configuration

---

**End of Docker Guide**

