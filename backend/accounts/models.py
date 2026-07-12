from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user per spec §4.4 (Users & social). is_deleted/deleted_at back
    the anonymize-and-retain account deletion flow (§5): the row survives
    deletion with PII scrubbed, so billing records stay attributable.
    """

    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username
