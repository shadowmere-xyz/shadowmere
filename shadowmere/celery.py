import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shadowmere.settings")

app = Celery("shadowmere")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
