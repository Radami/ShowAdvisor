"""
Celery app (spec §5): shared infrastructure for data sync jobs and, later,
notification dispatch. The `worker`/`beat` services join docker-compose in
task 3.6 — until then tasks are run manually (e.g. `.apply()` from a shell).
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("showadvisor")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
