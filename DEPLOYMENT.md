# Production Deployment Guide

**UJMP Backend - Production Deployment**

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Redis Setup](#redis-setup)
5. [Application Server Configuration](#application-server-configuration)
6. [Celery Worker Configuration](#celery-worker-configuration)
7. [File Storage Setup](#file-storage-setup)
8. [Nginx Configuration](#nginx-configuration)
9. [SSL/TLS Configuration](#ssltls-configuration)
10. [Monitoring & Logging](#monitoring--logging)
11. [Environment Variables Checklist](#environment-variables-checklist)

---

## Prerequisites

### System Requirements

- **OS:** Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **Python:** 3.12+
- **PostgreSQL:** 14+
- **Redis:** 6.0+
- **Nginx:** 1.18+ (as reverse proxy)
- **Supervisor:** For process management (optional)

### Required Packages

```bash
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3.12-dev
sudo apt-get install -y postgresql postgresql-contrib
sudo apt-get install -y redis-server
sudo apt-get install -y nginx
sudo apt-get install -y supervisor
sudo apt-get install -y build-essential libpq-dev
```

---

## Environment Setup

### 1. Create Application User

```bash
sudo adduser --system --group --home /opt/ujmp ujmp
sudo mkdir -p /opt/ujmp
sudo chown ujmp:ujmp /opt/ujmp
```

### 2. Clone Repository

```bash
cd /opt/ujmp
sudo -u ujmp git clone <repository-url> .
```

### 3. Create Virtual Environment

```bash
cd /opt/ujmp
sudo -u ujmp python3.12 -m venv venv
sudo -u ujmp venv/bin/pip install --upgrade pip
sudo -u ujmp venv/bin/pip install -r requirements.txt
```

---

## Database Setup

### 1. Create PostgreSQL Database

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE ujmp_production;
CREATE USER ujmp_user WITH PASSWORD 'secure_password_here';
ALTER ROLE ujmp_user SET client_encoding TO 'utf8';
ALTER ROLE ujmp_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE ujmp_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ujmp_production TO ujmp_user;
\q
```

### 2. Run Migrations

```bash
cd /opt/ujmp
sudo -u ujmp venv/bin/python manage.py migrate
```

### 3. Create Superuser

```bash
sudo -u ujmp venv/bin/python manage.py createsuperuser
```

---

## Redis Setup

### 1. Configure Redis

Edit `/etc/redis/redis.conf`:

```conf
bind 127.0.0.1
port 6379
requirepass your_redis_password_here
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### 2. Restart Redis

```bash
sudo systemctl restart redis
sudo systemctl enable redis
```

### 3. Test Redis Connection

```bash
redis-cli -a your_redis_password_here ping
```

---

## Application Server Configuration

### Option 1: Gunicorn (Recommended for Production)

#### 1. Create Gunicorn Configuration

Create `/opt/ujmp/gunicorn_config.py`:

```python
"""Gunicorn configuration file."""
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "/var/log/ujmp/gunicorn_access.log"
errorlog = "/var/log/ujmp/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "ujmp"

# Server mechanics
daemon = False
pidfile = "/var/run/ujmp/gunicorn.pid"
umask = 0
user = "ujmp"
group = "ujmp"
tmp_upload_dir = None

# SSL (if using SSL termination at Gunicorn)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    """Called when a worker receives INT or QUIT signal."""
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forking new master process")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")

def worker_abort(worker):
    """Called when a worker receives the ABRT signal."""
    worker.log.info("worker received ABRT signal")
```

#### 2. Create Log Directories

```bash
sudo mkdir -p /var/log/ujmp
sudo mkdir -p /var/run/ujmp
sudo chown -R ujmp:ujmp /var/log/ujmp
sudo chown -R ujmp:ujmp /var/run/ujmp
```

#### 3. Create Systemd Service

Create `/etc/systemd/system/ujmp.service`:

```ini
[Unit]
Description=UJMP Gunicorn daemon
After=network.target postgresql.service redis.service

[Service]
User=ujmp
Group=ujmp
WorkingDirectory=/opt/ujmp
Environment="PATH=/opt/ujmp/venv/bin"
ExecStart=/opt/ujmp/venv/bin/gunicorn \
    --config /opt/ujmp/gunicorn_config.py \
    ujmp.wsgi:application

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

#### 4. Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl start ujmp
sudo systemctl enable ujmp
sudo systemctl status ujmp
```

### Option 2: Uvicorn (Alternative - ASGI)

If using ASGI (for WebSocket support in future):

Create `/etc/systemd/system/ujmp-asgi.service`:

```ini
[Unit]
Description=UJMP Uvicorn ASGI daemon
After=network.target postgresql.service redis.service

[Service]
User=ujmp
Group=ujmp
WorkingDirectory=/opt/ujmp
Environment="PATH=/opt/ujmp/venv/bin"
ExecStart=/opt/ujmp/venv/bin/uvicorn \
    ujmp.asgi:application \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 4 \
    --log-level info

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

---

## Celery Worker Configuration

### 1. Create Celery Worker Service

Create `/etc/systemd/system/ujmp-celery.service`:

```ini
[Unit]
Description=UJMP Celery Worker
After=network.target redis.service postgresql.service

[Service]
Type=forking
User=ujmp
Group=ujmp
WorkingDirectory=/opt/ujmp
Environment="PATH=/opt/ujmp/venv/bin"
EnvironmentFile=/opt/ujmp/.env
ExecStart=/opt/ujmp/venv/bin/celery multi start worker1 \
    -A ujmp \
    --pidfile=/var/run/ujmp/celery_worker.pid \
    --logfile=/var/log/ujmp/celery_worker.log \
    --loglevel=info \
    --concurrency=4 \
    --time-limit=300 \
    --soft-time-limit=240

ExecStop=/opt/ujmp/venv/bin/celery multi stop worker1 \
    -A ujmp \
    --pidfile=/var/run/ujmp/celery_worker.pid

ExecReload=/opt/ujmp/venv/bin/celery multi restart worker1 \
    -A ujmp \
    --pidfile=/var/run/ujmp/celery_worker.pid \
    --logfile=/var/log/ujmp/celery_worker.log \
    --loglevel=info

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 2. Create Celery Beat Service (for scheduled tasks)

Create `/etc/systemd/system/ujmp-celery-beat.service`:

```ini
[Unit]
Description=UJMP Celery Beat
After=network.target redis.service postgresql.service

[Service]
Type=simple
User=ujmp
Group=ujmp
WorkingDirectory=/opt/ujmp
Environment="PATH=/opt/ujmp/venv/bin"
EnvironmentFile=/opt/ujmp/.env
ExecStart=/opt/ujmp/venv/bin/celery -A ujmp beat \
    --pidfile=/var/run/ujmp/celery_beat.pid \
    --logfile=/var/log/ujmp/celery_beat.log \
    --loglevel=info

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 3. Start Celery Services

```bash
sudo systemctl daemon-reload
sudo systemctl start ujmp-celery
sudo systemctl start ujmp-celery-beat
sudo systemctl enable ujmp-celery
sudo systemctl enable ujmp-celery-beat
```

---

## File Storage Setup

### Option 1: Local Storage (Development/Testing)

```bash
sudo mkdir -p /opt/ujmp/media
sudo mkdir -p /opt/ujmp/staticfiles
sudo chown -R ujmp:ujmp /opt/ujmp/media
sudo chown -R ujmp:ujmp /opt/ujmp/staticfiles
```

### Option 2: S3-Compatible Storage (Production)

Configure MinIO or AWS S3:

1. Set environment variables (see checklist below)
2. Ensure `USE_S3=True` in `.env`
3. Configure bucket policies for public read access to media

---

## Nginx Configuration

### 1. Create Nginx Configuration

Create `/etc/nginx/sites-available/ujmp`:

```nginx
upstream ujmp_backend {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name api.ujmp.example.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.ujmp.example.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.ujmp.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.ujmp.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Client body size (for file uploads)
    client_max_body_size 50M;
    
    # Logging
    access_log /var/log/nginx/ujmp_access.log;
    error_log /var/log/nginx/ujmp_error.log;
    
    # Static files
    location /static/ {
        alias /opt/ujmp/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /opt/ujmp/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
    
    # API endpoints
    location /api/ {
        proxy_pass http://ujmp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Certificate verification (public)
    location /verify/ {
        proxy_pass http://ujmp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check
    location /health/ {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

### 2. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/ujmp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## SSL/TLS Configuration

### Using Let's Encrypt (Certbot)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d api.ujmp.example.com
sudo certbot renew --dry-run
```

### Auto-renewal

Certbot creates a systemd timer automatically. Verify:

```bash
sudo systemctl status certbot.timer
```

---

## Monitoring & Logging

### 1. Log Rotation

Create `/etc/logrotate.d/ujmp`:

```
/var/log/ujmp/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ujmp ujmp
    sharedscripts
    postrotate
        systemctl reload ujmp > /dev/null 2>&1 || true
        systemctl reload ujmp-celery > /dev/null 2>&1 || true
    endscript
}
```

### 2. Health Check Endpoint

Add to `ujmp/urls.py`:

```python
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'healthy'})

urlpatterns += [
    path('health/', health_check, name='health'),
]
```

---

## Environment Variables Checklist

Create `/opt/ujmp/.env` with the following variables:

### Required Variables

```bash
# Django
SECRET_KEY=<generate_secure_key>
DEBUG=False
ALLOWED_HOSTS=api.ujmp.example.com,127.0.0.1

# Database
DB_NAME=ujmp_production
DB_USER=ujmp_user
DB_PASSWORD=<secure_password>
DB_HOST=localhost
DB_PORT=5432

# Redis/Celery
CELERY_BROKER_URL=redis://:your_redis_password@localhost:6379/0
CELERY_RESULT_BACKEND=redis://:your_redis_password@localhost:6379/0

# CORS
CORS_ALLOWED_ORIGINS=https://ujmp.example.com,https://www.ujmp.example.com

# File Storage
USE_S3=True
AWS_ACCESS_KEY_ID=<minio_or_s3_key>
AWS_SECRET_ACCESS_KEY=<minio_or_s3_secret>
AWS_STORAGE_BUCKET_NAME=ujmp-media
AWS_S3_ENDPOINT_URL=https://s3.example.com
AWS_S3_CUSTOM_DOMAIN=<optional_cdn_domain>

# Payment Providers
PAYME_MERCHANT_ID=<payme_merchant_id>
PAYME_SECRET_KEY=<payme_secret_key>
CLICK_MERCHANT_ID=<click_merchant_id>
CLICK_SECRET_KEY=<click_secret_key>

# Certificate
CERTIFICATE_ISSUER_NAME=Unified Journal Management Platform
CERTIFICATE_VERIFICATION_BASE_URL=https://api.ujmp.example.com/verify/certificate

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DEFAULT_FROM_EMAIL=noreply@ujmp.example.com
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<smtp_username>
EMAIL_HOST_PASSWORD=<smtp_password>
```

### Generate Secret Key

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Set Permissions

```bash
sudo chmod 600 /opt/ujmp/.env
sudo chown ujmp:ujmp /opt/ujmp/.env
```

---

## Deployment Checklist

- [ ] All prerequisites installed
- [ ] Application user created
- [ ] Repository cloned
- [ ] Virtual environment created and dependencies installed
- [ ] Database created and migrations run
- [ ] Superuser created
- [ ] Redis configured and running
- [ ] Environment variables set
- [ ] Gunicorn/Uvicorn service configured and running
- [ ] Celery worker and beat services running
- [ ] Nginx configured and running
- [ ] SSL certificate installed
- [ ] Static files collected (`python manage.py collectstatic --noinput`)
- [ ] Log directories created with proper permissions
- [ ] Health check endpoint accessible
- [ ] All services enabled to start on boot

---

## Post-Deployment Verification

1. **Check Services:**
   ```bash
   sudo systemctl status ujmp
   sudo systemctl status ujmp-celery
   sudo systemctl status ujmp-celery-beat
   sudo systemctl status nginx
   sudo systemctl status postgresql
   sudo systemctl status redis
   ```

2. **Test API:**
   ```bash
   curl https://api.ujmp.example.com/health/
   curl https://api.ujmp.example.com/api/journals/
   ```

3. **Check Logs:**
   ```bash
   sudo tail -f /var/log/ujmp/gunicorn_error.log
   sudo tail -f /var/log/ujmp/celery_worker.log
   ```

---

## Troubleshooting

### Gunicorn won't start
- Check logs: `sudo journalctl -u ujmp -n 50`
- Verify permissions on log directories
- Check database connectivity

### Celery tasks not executing
- Verify Redis connection: `redis-cli -a password ping`
- Check Celery logs: `sudo tail -f /var/log/ujmp/celery_worker.log`
- Verify environment variables are loaded

### 502 Bad Gateway
- Check Gunicorn is running: `sudo systemctl status ujmp`
- Verify Nginx can reach backend: `curl http://127.0.0.1:8000/health/`
- Check Nginx error log: `sudo tail -f /var/log/nginx/ujmp_error.log`

---

**End of Deployment Guide**

