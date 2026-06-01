import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("student_management")

# Read CELERY_* keys from Django settings.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks.py modules across installed apps.
app.autodiscover_tasks()
