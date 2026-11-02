import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_check.settings')

app = Celery('health_check')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
