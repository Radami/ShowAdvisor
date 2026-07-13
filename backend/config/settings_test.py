"""
Test settings: the real settings with the knobs that make tests fast and
hermetic — in-memory cache (no Redis), eager Celery, cheap password hashing.

The database stays PostgreSQL: search depends on pg_trgm (spec §4.6), which
SQLite can't emulate, so tests run inside the compose stack like the app.
"""

from .settings import *  # noqa: F401,F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

CELERY_TASK_ALWAYS_EAGER = True
