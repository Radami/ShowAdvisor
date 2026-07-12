# Ensure @shared_task binds to our Celery app whenever Django loads.
from .celery import app as celery_app

__all__ = ["celery_app"]
