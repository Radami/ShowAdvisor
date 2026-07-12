from django.conf import settings
from django.db import models


class DeviceToken(models.Model):
    """
    FCM registration token (spec §4.4). A user can have several (multi-device,
    §5); the dispatch task deletes rows FCM reports as invalid so stale tokens
    don't accumulate. Unique globally: a device belongs to one account at a
    time — re-registration after a user switch reassigns the row.
    """

    class Platform(models.TextChoices):
        ANDROID = "android"
        IOS = "ios"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="device_tokens"
    )
    # TextField: FCM says treat tokens as opaque and up to ~4KB.
    token = models.TextField(unique=True)
    platform = models.CharField(max_length=10, choices=Platform.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} [{self.platform}]"
