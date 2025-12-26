# Health Check Endpoints

The UJMP backend provides comprehensive health check endpoints similar to Spring Boot Actuator.

## Endpoints

### 1. `/health/` - Comprehensive Health Check

Returns detailed status of all platform services.

**Response Format:**
```json
{
  "status": "UP",
  "timestamp": "2025-12-26T10:30:00.123456+00:00",
  "version": "1.0.0",
  "components": {
    "db": {
      "status": "UP",
      "details": {
        "database": "ujmp_user",
        "engine": "postgresql"
      }
    },
    "redis": {
      "status": "UP",
      "details": {
        "backend": "redis",
        "host": "redis"
      }
    },
    "celery": {
      "status": "UP",
      "details": {
        "workers": 1,
        "active_tasks": 0,
        "registered_tasks": 15
      }
    },
    "storage": {
      "status": "UP",
      "details": {
        "type": "S3",
        "bucket": "ujmp-media",
        "endpoint": "http://localhost:9000"
      }
    },
    "disk": {
      "status": "UP",
      "details": {
        "total_gb": 100.0,
        "used_gb": 50.0,
        "free_gb": 50.0,
        "percent_used": 50.0
      }
    }
  }
}
```

**HTTP Status Codes:**
- `200 OK`: All services are UP
- `503 Service Unavailable`: One or more services are DOWN

**Component Status Values:**
- `UP`: Service is healthy and operational
- `DOWN`: Service is unavailable or failing
- `WARN`: Service is operational but has warnings (e.g., high disk usage)
- `UNKNOWN`: Service status cannot be determined

### 2. `/health/live/` - Liveness Probe

Simple endpoint to check if the application is running. Always returns `200 OK` if the application process is alive.

**Response:**
```json
{
  "status": "alive"
}
```

**Use Cases:**
- Kubernetes liveness probe
- Docker health check
- Load balancer health check

### 3. `/health/ready/` - Readiness Probe

Checks if the application is ready to serve traffic. Verifies critical dependencies (database, Redis).

**Response Format:**
```json
{
  "status": "ready",
  "checks": {
    "database": {
      "status": "UP",
      "details": {
        "database": "ujmp_user",
        "engine": "postgresql"
      }
    },
    "redis": {
      "status": "UP",
      "details": {
        "backend": "redis",
        "host": "redis"
      }
    }
  }
}
```

**HTTP Status Codes:**
- `200 OK`: Application is ready to serve traffic
- `503 Service Unavailable`: Application is not ready (critical dependencies down)

**Use Cases:**
- Kubernetes readiness probe
- Load balancer traffic routing
- Deployment verification

## Component Checks

### Database Check
- Tests database connectivity
- Executes a simple query (`SELECT 1`)
- Returns database name and engine type

### Redis Check
- Tests Redis connectivity via Django cache
- Performs read/write/delete operations
- Returns Redis connection details

### Celery Check
- Checks for active Celery workers
- Counts active tasks
- Lists registered tasks
- Returns worker count and task statistics

### Storage Check
- **S3/MinIO**: Verifies S3-compatible storage connectivity
- **Filesystem**: Checks local filesystem writability
- Returns storage type and configuration

### Disk Space Check
- Monitors disk usage
- Returns total, used, and free space in GB
- Status:
  - `UP`: Disk usage < 90%
  - `WARN`: Disk usage 90-95%
  - `DOWN`: Disk usage > 95%

## Usage Examples

### Docker Health Check

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/').read()"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Kubernetes Probes

```yaml
livenessProbe:
  httpGet:
    path: /health/live/
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready/
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

### Load Balancer Health Check

```nginx
location /health/ {
    proxy_pass http://ujmp_backend;
    access_log off;
}
```

### Monitoring Integration

```bash
# Check health status
curl http://localhost:8000/health/

# Check if ready
curl http://localhost:8000/health/ready/

# Check if alive
curl http://localhost:8000/health/live/
```

## Response Status Aggregation

The overall `status` field in `/health/` is determined as follows:

1. If any component is `DOWN`, overall status is `DOWN`
2. If all components are `UP`, overall status is `UP`
3. If any component is `WARN` but none are `DOWN`, overall status is `UP` (with warnings in component details)
4. `UNKNOWN` components don't affect overall status

## Error Handling

All health checks include error handling:
- Database connection failures are caught and reported
- Redis connection failures are caught and reported
- Celery worker unavailability is detected
- Storage connectivity issues are identified
- Disk space checks gracefully handle permission errors

## Performance

Health checks are designed to be fast:
- Database check: < 100ms
- Redis check: < 50ms
- Celery check: < 2s (with timeout)
- Storage check: < 500ms
- Disk check: < 100ms

**Total expected response time:** < 3 seconds

## Security

Health check endpoints are:
- Publicly accessible (no authentication required)
- Safe for load balancer monitoring
- Do not expose sensitive information
- Return only operational status

---

**Last Updated:** December 26, 2025

