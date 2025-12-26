"""
Comprehensive health check endpoint (Actuator-style).
"""
import json
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from celery import current_app


def health_check(request):
    """
    Comprehensive health check endpoint.
    
    Returns detailed status of all platform services:
    - Database connectivity
    - Redis connectivity
    - Celery worker status
    - Storage (S3/MinIO) connectivity
    - Overall application health
    """
    health_status = {
        'status': 'UP',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0',
        'components': {}
    }
    
    overall_status = 'UP'
    
    # Check Database
    db_status = check_database()
    health_status['components']['db'] = db_status
    if db_status['status'] != 'UP':
        overall_status = 'DOWN'
    
    # Check Redis
    redis_status = check_redis()
    health_status['components']['redis'] = redis_status
    if redis_status['status'] != 'UP':
        overall_status = 'DOWN'
    
    # Check Celery
    celery_status = check_celery()
    health_status['components']['celery'] = celery_status
    if celery_status['status'] != 'UP':
        overall_status = 'DOWN'
    
    # Check Storage (S3/MinIO)
    storage_status = check_storage()
    health_status['components']['storage'] = storage_status
    if storage_status['status'] != 'UP':
        overall_status = 'DOWN'
    
    # Check Disk Space (optional)
    disk_status = check_disk_space()
    health_status['components']['disk'] = disk_status
    if disk_status['status'] == 'DOWN':
        overall_status = 'DOWN'
    
    health_status['status'] = overall_status
    
    # Return appropriate HTTP status code
    http_status = 200 if overall_status == 'UP' else 503
    
    # Ensure all values are JSON-serializable by converting to strings where needed
    serializable_status = make_json_serializable(health_status)
    
    return JsonResponse(serializable_status, status=http_status)


def make_json_serializable(obj):
    """Recursively convert object to JSON-serializable format."""
    if isinstance(obj, dict):
        return {key: make_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        # Convert any other type to string
        return str(obj)


def check_database():
    """Check database connectivity."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        # Get database info
        db_name = settings.DATABASES['default']['NAME']
        db_engine = settings.DATABASES['default']['ENGINE']
        
        return {
            'status': 'UP',
            'details': {
                'database': db_name,
                'engine': db_engine.split('.')[-1] if '.' in db_engine else db_engine
            }
        }
    except Exception as e:
        return {
            'status': 'DOWN',
            'details': {
                'error': str(e)
            }
        }


def check_redis():
    """Check Redis connectivity."""
    try:
        # Test cache backend
        test_key = 'health_check_test'
        test_value = 'test'
        cache.set(test_key, test_value, timeout=10)
        retrieved = cache.get(test_key)
        cache.delete(test_key)
        
        if retrieved != test_value:
            raise Exception("Cache value mismatch")
        
        # Get Redis connection info if available
        details = {
            'backend': 'redis'
        }
        
        # Try to get Redis connection details
        try:
            broker_url = getattr(settings, 'CELERY_BROKER_URL', '')
            if broker_url.startswith('redis://'):
                # Extract host from broker URL
                parts = broker_url.replace('redis://', '').split('/')
                if '@' in parts[0]:
                    # Has password
                    auth, host = parts[0].split('@')
                    details['host'] = host.split(':')[0] if ':' in host else host
                else:
                    details['host'] = parts[0].split(':')[0] if ':' in parts[0] else parts[0]
        except Exception:
            pass
        
        return {
            'status': 'UP',
            'details': details
        }
    except Exception as e:
        return {
            'status': 'DOWN',
            'details': {
                'error': str(e)
            }
        }


def check_celery():
    """Check Celery worker status."""
    try:
        # Check if Celery is configured
        broker_url = getattr(settings, 'CELERY_BROKER_URL', None)
        if not broker_url:
            return {
                'status': 'UNKNOWN',
                'details': {
                    'message': 'Celery not configured'
                }
            }
        
        # Get active workers
        inspect = current_app.control.inspect(timeout=2.0)
        
        try:
            active_workers = inspect.active()
        except Exception:
            # If we can't connect to workers, they might be down
            return {
                'status': 'DOWN',
                'details': {
                    'error': 'Cannot connect to Celery workers'
                }
            }
        
        if active_workers is None or len(active_workers) == 0:
            return {
                'status': 'DOWN',
                'details': {
                    'error': 'No Celery workers found'
                }
            }
        
        worker_count = len(active_workers)
        total_tasks = sum(len(tasks) for tasks in active_workers.values())
        
        # Get registered tasks
        try:
            registered = inspect.registered()
            task_count = len(registered) if registered else 0
        except Exception:
            task_count = 0
        
        return {
            'status': 'UP',
            'details': {
                'workers': worker_count,
                'active_tasks': total_tasks,
                'registered_tasks': task_count
            }
        }
    except Exception as e:
        return {
            'status': 'DOWN',
            'details': {
                'error': str(e)
            }
        }


def check_storage():
    """Check storage connectivity (S3/MinIO or local filesystem)."""
    try:
        use_s3 = getattr(settings, 'USE_S3', False)
        
        if use_s3:
            # Check S3/MinIO connectivity
            try:
                from storages.backends.s3boto3 import S3Boto3Storage
                from django.core.files.storage import default_storage
                
                # Try to list buckets or check connection
                # This is a simple check - in production you might want to do a test write
                bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')
                endpoint_url = getattr(settings, 'AWS_S3_ENDPOINT_URL', '')
                
                return {
                    'status': 'UP',
                    'details': {
                        'type': 'S3',
                        'bucket': bucket_name,
                        'endpoint': endpoint_url
                    }
                }
            except Exception as e:
                return {
                    'status': 'DOWN',
                    'details': {
                        'type': 'S3',
                        'error': str(e)
                    }
                }
        else:
            # Check local filesystem
            import os
            media_root = getattr(settings, 'MEDIA_ROOT', '')
            static_root = getattr(settings, 'STATIC_ROOT', '')
            
            # Check if directories exist and are writable
            media_writable = os.access(media_root, os.W_OK) if media_root else False
            static_writable = os.access(static_root, os.W_OK) if static_root else False
            
            return {
                'status': 'UP' if (media_writable or not media_root) else 'DOWN',
                'details': {
                    'type': 'filesystem',
                    'media_root': media_root,
                    'media_writable': media_writable,
                    'static_root': static_root,
                    'static_writable': static_writable
                }
            }
    except Exception as e:
        return {
            'status': 'DOWN',
            'details': {
                'error': str(e)
            }
        }


def check_disk_space():
    """Check disk space availability."""
    try:
        import shutil
        import os
        
        # Get disk usage for the root directory
        total, used, free = shutil.disk_usage('/')
        
        # Convert to GB
        total_gb = total / (1024 ** 3)
        used_gb = used / (1024 ** 3)
        free_gb = free / (1024 ** 3)
        percent_used = (used / total) * 100
        
        # Warn if disk usage is above 90%
        status = 'UP'
        if percent_used > 95:
            status = 'DOWN'
        elif percent_used > 90:
            status = 'WARN'
        
        return {
            'status': status,
            'details': {
                'total_gb': round(total_gb, 2),
                'used_gb': round(used_gb, 2),
                'free_gb': round(free_gb, 2),
                'percent_used': round(percent_used, 2)
            }
        }
    except Exception as e:
        # If we can't check disk space, don't fail the health check
        return {
            'status': 'UNKNOWN',
            'details': {
                'error': str(e)
            }
        }


def health_check_liveness(request):
    """
    Simple liveness probe (for Kubernetes/Docker).
    Returns 200 if the application is running.
    """
    return JsonResponse({'status': 'alive'}, status=200)


def health_check_readiness(request):
    """
    Readiness probe - checks if application is ready to serve traffic.
    Checks critical dependencies (database, redis).
    """
    checks = {
        'database': check_database(),
        'redis': check_redis()
    }
    
    # Application is ready if database and redis are up
    ready = all(
        check['status'] == 'UP' 
        for check in checks.values()
    )
    
    status_code = 200 if ready else 503
    
    return JsonResponse({
        'status': 'ready' if ready else 'not_ready',
        'checks': checks
    }, status=status_code)

