# Security Hardening Guide

**UJMP Backend - Security Configuration**

---

## Table of Contents

1. [Rate Limiting](#rate-limiting)
2. [CORS Configuration](#cors-configuration)
3. [Webhook Security](#webhook-security)
4. [Media Access Rules](#media-access-rules)
5. [Authentication Security](#authentication-security)
6. [Database Security](#database-security)
7. [SSL/TLS Configuration](#ssltls-configuration)
8. [Security Headers](#security-headers)
9. [Input Validation](#input-validation)
10. [Audit Logging](#audit-logging)

---

## Rate Limiting

### Configured Rate Limits

The following rate limits are enforced:

- **Anonymous Users:** 100 requests/hour
- **Authenticated Users:** 1000 requests/hour
- **Article Submission:** 5 submissions/hour per user
- **Workflow Actions:** 20 actions/hour per user
- **Public API:** 100 requests/hour per IP
- **Webhooks:** 1000 requests/hour per IP
- **Certificate Verification:** 60 verifications/minute per IP

### Customization

Rate limits can be adjusted in `ujmp/settings.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'article_submission': '5/hour',
        'workflow_action': '20/hour',
        # ... adjust as needed
    },
}
```

### Rate Limit Headers

When rate limits are exceeded, responses include:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
Retry-After: 3600
```

---

## CORS Configuration

### Production CORS Settings

**CRITICAL:** In production, restrict CORS to specific origins only.

```python
# .env
CORS_ALLOWED_ORIGINS=https://ujmp.example.com,https://www.ujmp.example.com
```

### CORS Security Headers

- `Access-Control-Allow-Credentials: true` - Allows cookies/auth headers
- `Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS`
- `Access-Control-Allow-Headers: authorization, content-type`

### Development vs Production

**Development:**
```python
CORS_ALLOWED_ORIGINS = ['http://localhost:3000', 'http://localhost:5173']
```

**Production:**
```python
CORS_ALLOWED_ORIGINS = ['https://ujmp.example.com']
```

**NEVER use:**
```python
CORS_ALLOW_ALL_ORIGINS = True  # NEVER in production!
```

---

## Webhook Security

### 1. IP Whitelisting

Webhook endpoints are restricted to whitelisted IPs.

**Configuration:**

```bash
# .env
WEBHOOK_ALLOWED_IPS=203.0.113.0/24,198.51.100.0/24
```

Supports:
- Single IPs: `203.0.113.1`
- CIDR blocks: `203.0.113.0/24`

### 2. Signature Verification

All webhooks MUST verify signatures:

**Payme:**
```python
# Verify HMAC-SHA256 signature
signature = request.headers.get('X-Payme-Signature')
verify_payme_signature(data, signature)
```

**Click:**
```python
# Verify HMAC-SHA256 signature
signature = request.headers.get('X-Click-Signature')
verify_click_signature(data, signature)
```

### 3. Webhook Security Checklist

- [ ] IP whitelist configured
- [ ] Signature verification enabled
- [ ] HTTPS only (no HTTP)
- [ ] Idempotent processing (duplicate detection)
- [ ] Rate limiting enabled
- [ ] CSRF exemption (webhooks only)
- [ ] Request logging enabled

### 4. Testing Webhooks

Use ngrok or similar for local testing:

```bash
ngrok http 8000
# Use ngrok URL in payment provider webhook configuration
```

---

## Media Access Rules

### File Upload Restrictions

**Maximum File Size:** 50MB (configured in Nginx)

**Allowed File Types:**
- Manuscripts: PDF, DOCX
- Logos: JPG, PNG, GIF

**Validation:**

```python
# In serializers/models
def validate_manuscript_file(self, value):
    if value.size > 50 * 1024 * 1024:  # 50MB
        raise ValidationError('File size exceeds 50MB')
    if not value.name.endswith(('.pdf', '.docx')):
        raise ValidationError('Only PDF and DOCX files allowed')
    return value
```

### Media File Access

**Public Media:**
- Journal logos: Public read access
- Published certificates: Authenticated download

**Private Media:**
- Manuscript files: Author/Reviewer/Admin only
- Draft certificates: Author only

### S3/MinIO Security

**Bucket Policies:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::ujmp-media/journals/logos/*"
    },
    {
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::ujmp-media/articles/manuscripts/*",
      "Condition": {
        "StringNotEquals": {
          "aws:Referer": "https://ujmp.example.com"
        }
      }
    }
  ]
}
```

---

## Authentication Security

### JWT Token Security

**Token Lifetime:**
- Access Token: 1 hour
- Refresh Token: 7 days

**Token Storage:**
- **Frontend:** Store in httpOnly cookies (recommended) or secure localStorage
- **Never:** Store in plain localStorage without encryption

**Token Rotation:**
- Refresh tokens are rotated on use
- Old refresh tokens are blacklisted

### Password Security

**Requirements:**
- Minimum length: 8 characters (enforced by Django validators)
- Password hashing: PBKDF2 (Django default)
- Password reset: Token-based, expires in 24 hours

**Password Reset Security:**
```python
# In settings.py
PASSWORD_RESET_TIMEOUT = 86400  # 24 hours
```

### Session Security

**Production Settings:**
```python
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True  # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400  # 24 hours
```

---

## Database Security

### PostgreSQL Security

**Connection Security:**
```python
# Use SSL for database connections
DATABASES = {
    'default': {
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}
```

**User Permissions:**
- Application user: Limited to specific database
- No SUPERUSER privileges
- Read-only user for backups

**Backup Security:**
- Encrypted backups
- Off-site storage
- Regular rotation

### SQL Injection Prevention

**Django ORM:**
- Always use ORM queries (parameterized)
- Never use raw SQL with user input
- Use `extra()` and `raw()` with caution

**Example (Safe):**
```python
Article.objects.filter(title__icontains=user_input)  # Safe
```

**Example (Unsafe):**
```python
Article.objects.extra(where=[f"title = '{user_input}'"])  # UNSAFE
```

---

## SSL/TLS Configuration

### Nginx SSL Configuration

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
```

### Certificate Management

- Use Let's Encrypt for free certificates
- Auto-renewal configured
- HSTS enabled (1 year)

---

## Security Headers

### HTTP Security Headers

Configured in Nginx:

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

### Django Security Settings

```python
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
```

---

## Input Validation

### Serializer Validation

All user input is validated through DRF serializers:

```python
class ArticleCreateSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=500)
    abstract = serializers.CharField()
    
    def validate_title(self, value):
        # Custom validation
        if len(value) < 10:
            raise serializers.ValidationError("Title too short")
        return value
```

### File Upload Validation

```python
def validate_manuscript_file(self, value):
    # Size check
    if value.size > 50 * 1024 * 1024:
        raise ValidationError('File too large')
    
    # Type check
    allowed_types = ['.pdf', '.docx']
    if not any(value.name.lower().endswith(ext) for ext in allowed_types):
        raise ValidationError('Invalid file type')
    
    return value
```

### SQL Injection Prevention

- Use Django ORM exclusively
- Parameterized queries for raw SQL
- Input sanitization in serializers

---

## Audit Logging

### Critical Actions Logged

All critical actions are logged to `AuditLog`:

- Status changes
- Review decisions
- Payment confirmations
- Certificate issuance/revocation
- Admin overrides

### Log Retention

- **Audit Logs:** Retained indefinitely (database)
- **Application Logs:** 14 days rotation
- **Access Logs:** 30 days rotation

### Log Security

- Logs stored securely
- Access restricted to admins
- No sensitive data in logs (passwords, tokens)

---

## Security Checklist

### Pre-Production

- [ ] DEBUG = False
- [ ] SECRET_KEY changed from default
- [ ] CORS_ALLOWED_ORIGINS restricted
- [ ] WEBHOOK_ALLOWED_IPS configured
- [ ] SSL/TLS enabled
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Database SSL enabled
- [ ] Password requirements enforced
- [ ] File upload restrictions configured
- [ ] Audit logging enabled

### Ongoing

- [ ] Regular security updates
- [ ] Monitor audit logs
- [ ] Review rate limit violations
- [ ] Check webhook signatures
- [ ] Verify SSL certificate validity
- [ ] Review access logs
- [ ] Update dependencies regularly

---

## Incident Response

### Security Incident Procedure

1. **Identify:** Detect security issue
2. **Contain:** Isolate affected systems
3. **Assess:** Determine scope and impact
4. **Remediate:** Fix vulnerability
5. **Document:** Log incident and response
6. **Notify:** Inform stakeholders if required

### Contact Information

- **Security Team:** security@ujmp.example.com
- **Emergency:** +1-XXX-XXX-XXXX

---

**End of Security Guide**

