import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "skillexa.settings")  # Change "your_project" to your actual project name

celery_app = Celery("skillexa")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()