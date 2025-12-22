"""
WSGI config for UJMP project.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ujmp.settings')

application = get_wsgi_application()

