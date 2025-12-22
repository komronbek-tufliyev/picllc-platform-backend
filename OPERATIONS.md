# Operational Documentation

**UJMP Backend - Operations Guide**

---

## Table of Contents

1. [Deployment Steps](#deployment-steps)
2. [Rollback Strategy](#rollback-strategy)
3. [Celery Task Recovery](#celery-task-recovery)
4. [Certificate Revocation Procedure](#certificate-revocation-procedure)
5. [Database Maintenance](#database-maintenance)
6. [Monitoring & Alerts](#monitoring--alerts)
7. [Backup & Recovery](#backup--recovery)
8. [Troubleshooting Guide](#troubleshooting-guide)

---

## Deployment Steps

### Pre-Deployment Checklist

- [ ] Code reviewed and approved
- [ ] Tests passing (`python manage.py test`)
- [ ] Database migrations reviewed
- [ ] Environment variables updated
- [ ] Dependencies updated (`pip install -r requirements.txt`)
- [ ] Backup current database
- [ ] Notify team of deployment window

### Standard Deployment Procedure

#### 1. Prepare Deployment Branch

```bash
git checkout main
git pull origin main
git checkout -b deploy/v1.x.x
```

#### 2. Run Tests

```bash
python manage.py test --settings=ujmp.test_settings
```

#### 3. Check Migrations

```bash
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
```

#### 4. Backup Database

```bash
# Create backup
pg_dump -U ujmp_user -d ujmp_production > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh backup_*.sql
```

#### 5. Deploy Code

```bash
# On server
cd /opt/ujmp
sudo -u ujmp git fetch origin
sudo -u ujmp git checkout deploy/v1.x.x
sudo -u ujmp venv/bin/pip install -r requirements.txt
```

#### 6. Run Migrations

```bash
sudo -u ujmp venv/bin/python manage.py migrate
```

#### 7. Collect Static Files

```bash
sudo -u ujmp venv/bin/python manage.py collectstatic --noinput
```

#### 8. Restart Services

```bash
# Restart in order
sudo systemctl restart ujmp-celery-beat
sudo systemctl restart ujmp-celery
sudo systemctl restart ujmp
sudo systemctl reload nginx
```

#### 9. Verify Deployment

```bash
# Check services
sudo systemctl status ujmp
sudo systemctl status ujmp-celery
sudo systemctl status ujmp-celery-beat

# Test endpoints
curl https://api.ujmp.example.com/health/
curl https://api.ujmp.example.com/api/journals/

# Check logs
sudo tail -f /var/log/ujmp/gunicorn_error.log
```

#### 10. Post-Deployment

- [ ] Verify all endpoints working
- [ ] Check Celery tasks executing
- [ ] Monitor error logs for 30 minutes
- [ ] Update deployment log

### Zero-Downtime Deployment

For zero-downtime deployments:

1. **Use Blue-Green Deployment:**
   - Deploy to secondary server
   - Switch traffic via load balancer
   - Keep old server running for rollback

2. **Database Migrations:**
   - Use backward-compatible migrations
   - Deploy code first, then migrate
   - Or use feature flags

3. **Service Restart:**
   ```bash
   # Graceful restart (Gunicorn)
   sudo systemctl reload ujmp  # Sends HUP signal
   ```

---

## Rollback Strategy

### Quick Rollback Procedure

#### 1. Identify Issue

```bash
# Check logs
sudo tail -f /var/log/ujmp/gunicorn_error.log
sudo journalctl -u ujmp -n 100
```

#### 2. Stop Services

```bash
sudo systemctl stop ujmp
sudo systemctl stop ujmp-celery
sudo systemctl stop ujmp-celery-beat
```

#### 3. Rollback Code

```bash
cd /opt/ujmp
sudo -u ujmp git checkout <previous_commit_hash>
sudo -u ujmp venv/bin/pip install -r requirements.txt
```

#### 4. Rollback Database (if needed)

```bash
# Restore from backup
psql -U ujmp_user -d ujmp_production < backup_YYYYMMDD_HHMMSS.sql
```

#### 5. Restart Services

```bash
sudo systemctl start ujmp
sudo systemctl start ujmp-celery
sudo systemctl start ujmp-celery-beat
```

#### 6. Verify Rollback

```bash
curl https://api.ujmp.example.com/health/
sudo systemctl status ujmp
```

### Database Migration Rollback

If migration caused issues:

```bash
# Rollback last migration
python manage.py migrate <app_name> <previous_migration>

# Example
python manage.py migrate articles 0005_previous_migration
```

### Rollback Decision Matrix

| Issue Type | Rollback Action | Time Estimate |
|------------|----------------|---------------|
| Code bug | Rollback code only | 5 minutes |
| Migration failure | Rollback code + database | 15 minutes |
| Performance degradation | Rollback code, investigate | 10 minutes |
| Data corruption | Rollback code + database restore | 30 minutes |

---

## Celery Task Recovery

### Failed Task Recovery

#### 1. Identify Failed Tasks

```bash
# Check Celery logs
sudo tail -f /var/log/ujmp/celery_worker.log | grep ERROR

# Or use Flower (if installed)
# Access http://localhost:5555
```

#### 2. Retry Failed Tasks

**Via Django Shell:**

```python
from apps.certificates.tasks import generate_certificate_pdf
from apps.certificates.models import Certificate

# Find failed certificate
certificate = Certificate.objects.get(certificate_id='...')

# Retry task
generate_certificate_pdf.delay(str(certificate.certificate_id))
```

**Via Celery CLI:**

```bash
# List failed tasks
celery -A ujmp inspect failed

# Retry specific task
celery -A ujmp retry <task_id>
```

#### 3. Bulk Retry Failed Tasks

```python
# Django management command
from django.core.management.base import BaseCommand
from apps.certificates.models import Certificate
from apps.certificates.tasks import generate_certificate_pdf

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Find certificates without PDFs
        certificates = Certificate.objects.filter(
            pdf_file__isnull=True,
            article__status='PUBLISHED'
        )
        
        for cert in certificates:
            generate_certificate_pdf.delay(str(cert.certificate_id))
            self.stdout.write(f'Queued certificate {cert.certificate_id}')
```

#### 4. Task Monitoring

**Check Task Status:**

```bash
# Active tasks
celery -A ujmp inspect active

# Scheduled tasks
celery -A ujmp inspect scheduled

# Reserved tasks
celery -A ujmp inspect reserved
```

**Monitor Task Queue:**

```bash
# Install Flower
pip install flower

# Run Flower
celery -A ujmp flower --port=5555

# Access http://localhost:5555
```

### Common Task Issues

#### Certificate Generation Failed

**Symptoms:**
- Certificate exists but no PDF
- Article is PUBLISHED

**Recovery:**
```python
from apps.certificates.tasks import generate_certificate_pdf
certificate = Certificate.objects.get(certificate_id='...')
generate_certificate_pdf.delay(str(certificate.certificate_id))
```

#### Email Notification Failed

**Symptoms:**
- Action completed but no email sent
- Email task in failed state

**Recovery:**
```python
from apps.notifications.tasks import send_article_published_email
send_article_published_email.delay(article_id)
```

#### Payment Webhook Processing Failed

**Symptoms:**
- Payment received but invoice not updated
- Article status not changed to PAID

**Recovery:**
```python
from apps.payments.models import Invoice, Payment
from apps.payments.webhooks import PaymeWebhookView

# Manually process webhook data
invoice = Invoice.objects.get(invoice_number='...')
invoice.mark_as_paid(
    provider_transaction_id='TXN123',
    payment_provider='PAYME',
    user=None
)
```

---

## Certificate Revocation Procedure

### Standard Revocation

#### 1. Identify Certificate

```bash
# Via Django admin or API
GET /api/certificates/{id}/
```

#### 2. Revoke Certificate

**Via API (Admin):**

```bash
POST /api/certificates/{id}/revoke/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "reason": "Article retracted by author"
}
```

**Via Django Shell:**

```python
from apps.certificates.models import Certificate
from apps.accounts.models import User

certificate = Certificate.objects.get(certificate_id='...')
admin = User.objects.get(email='admin@example.com')

certificate.revoke(
    user=admin,
    reason='Article retracted by author'
)
```

#### 3. Verify Revocation

```bash
# Public verification should show revoked status
GET /verify/certificate/{certificate_id}/

# Response should include:
{
  "revoked": true,
  "status": "REVOKED"
}
```

### Bulk Revocation

**Revoke all certificates for an article:**

```python
from apps.articles.models import Article
from apps.certificates.models import Certificate

article = Article.objects.get(submission_id='...')
certificates = Certificate.objects.filter(article=article)

for cert in certificates:
    cert.revoke(user=admin, reason='Bulk revocation')
```

### Certificate Regeneration

**After revocation, regenerate if needed:**

```python
from apps.certificates.models import Certificate
from apps.certificates.tasks import generate_certificate_pdf

# Create new certificate
certificate = Certificate.objects.create(
    article=article,
    status=Certificate.Status.ACTIVE
)

# Generate PDF
generate_certificate_pdf.delay(str(certificate.certificate_id))
```

---

## Database Maintenance

### Regular Maintenance Tasks

#### 1. Vacuum Database

```bash
# Analyze tables
psql -U ujmp_user -d ujmp_production -c "VACUUM ANALYZE;"
```

#### 2. Check Database Size

```bash
psql -U ujmp_user -d ujmp_production -c "
SELECT 
    pg_size_pretty(pg_database_size('ujmp_production')) AS database_size;
"
```

#### 3. Check Table Sizes

```bash
psql -U ujmp_user -d ujmp_production -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

### Index Maintenance

**Check unused indexes:**

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Connection Monitoring

**Check active connections:**

```sql
SELECT 
    count(*) as total_connections,
    state,
    wait_event_type
FROM pg_stat_activity
WHERE datname = 'ujmp_production'
GROUP BY state, wait_event_type;
```

---

## Monitoring & Alerts

### Key Metrics to Monitor

1. **Application Health**
   - Response times
   - Error rates
   - Request throughput

2. **Database**
   - Connection pool usage
   - Query performance
   - Database size

3. **Celery**
   - Task queue length
   - Failed tasks
   - Task execution time

4. **System Resources**
   - CPU usage
   - Memory usage
   - Disk space

### Health Check Endpoint

```bash
# Basic health check
curl https://api.ujmp.example.com/health/

# Expected response: {"status": "healthy"}
```

### Log Monitoring

**Key Log Files:**

```bash
# Application logs
/var/log/ujmp/gunicorn_error.log
/var/log/ujmp/gunicorn_access.log

# Celery logs
/var/log/ujmp/celery_worker.log
/var/log/ujmp/celery_beat.log

# Nginx logs
/var/log/nginx/ujmp_access.log
/var/log/nginx/ujmp_error.log
```

**Monitor Logs:**

```bash
# Real-time monitoring
sudo tail -f /var/log/ujmp/gunicorn_error.log

# Search for errors
sudo grep -i error /var/log/ujmp/gunicorn_error.log | tail -20
```

### Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Error rate | > 1% | > 5% | Check logs |
| Response time | > 1s | > 5s | Investigate |
| Failed tasks | > 10/hour | > 50/hour | Review tasks |
| Disk usage | > 80% | > 90% | Cleanup |
| Memory usage | > 80% | > 90% | Restart services |

---

## Backup & Recovery

### Backup Strategy

#### 1. Database Backups

**Daily Backup Script:**

```bash
#!/bin/bash
# /opt/ujmp/scripts/backup_db.sh

BACKUP_DIR="/opt/backups/ujmp"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ujmp_db_$DATE.sql"

mkdir -p $BACKUP_DIR

pg_dump -U ujmp_user -d ujmp_production > $BACKUP_FILE

# Compress
gzip $BACKUP_FILE

# Keep only last 30 days
find $BACKUP_DIR -name "ujmp_db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

**Schedule with Cron:**

```bash
# Add to crontab
0 2 * * * /opt/ujmp/scripts/backup_db.sh
```

#### 2. Media Files Backup

```bash
# Backup media directory
tar -czf /opt/backups/ujmp/media_$(date +%Y%m%d).tar.gz /opt/ujmp/media/

# Or sync to S3
aws s3 sync /opt/ujmp/media/ s3://ujmp-backups/media/
```

#### 3. Configuration Backup

```bash
# Backup .env and configs
tar -czf /opt/backups/ujmp/config_$(date +%Y%m%d).tar.gz \
    /opt/ujmp/.env \
    /opt/ujmp/gunicorn_config.py \
    /etc/nginx/sites-available/ujmp
```

### Recovery Procedures

#### Database Recovery

```bash
# Stop application
sudo systemctl stop ujmp

# Restore database
psql -U ujmp_user -d ujmp_production < backup_file.sql

# Verify
psql -U ujmp_user -d ujmp_production -c "SELECT count(*) FROM articles;"

# Start application
sudo systemctl start ujmp
```

#### Media Files Recovery

```bash
# Extract backup
tar -xzf media_YYYYMMDD.tar.gz -C /opt/ujmp/

# Or restore from S3
aws s3 sync s3://ujmp-backups/media/ /opt/ujmp/media/

# Fix permissions
sudo chown -R ujmp:ujmp /opt/ujmp/media
```

---

## Troubleshooting Guide

### Common Issues

#### 1. Service Won't Start

**Check logs:**
```bash
sudo journalctl -u ujmp -n 50
```

**Common causes:**
- Database connection failure
- Missing environment variables
- Port already in use
- Permission issues

#### 2. Database Connection Errors

**Test connection:**
```bash
psql -U ujmp_user -d ujmp_production -c "SELECT 1;"
```

**Check PostgreSQL:**
```bash
sudo systemctl status postgresql
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### 3. Celery Tasks Not Executing

**Check Redis:**
```bash
redis-cli -a password ping
```

**Check Celery:**
```bash
celery -A ujmp inspect active
celery -A ujmp inspect stats
```

**Restart Celery:**
```bash
sudo systemctl restart ujmp-celery
```

#### 4. High Memory Usage

**Check processes:**
```bash
ps aux | grep -E 'gunicorn|celery|python'
```

**Restart services:**
```bash
sudo systemctl restart ujmp
sudo systemctl restart ujmp-celery
```

#### 5. Slow Response Times

**Check database queries:**
```sql
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

**Check Nginx:**
```bash
sudo tail -f /var/log/nginx/ujmp_access.log | grep -E "5[0-9]{2}"
```

---

## Emergency Contacts

- **On-Call Engineer:** +1-XXX-XXX-XXXX
- **Database Admin:** +1-XXX-XXX-XXXX
- **DevOps Team:** devops@ujmp.example.com

---

**End of Operations Guide**

