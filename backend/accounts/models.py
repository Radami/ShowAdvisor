from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Minimal custom user for Milestone 0 (spec §4.4): email, username,
    created_at. The full field set (is_deleted, deleted_at) comes in
    Milestone 1. Custom from day one so swapping AUTH_USER_MODEL never
    requires a painful mid-project migration.
    """

    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
