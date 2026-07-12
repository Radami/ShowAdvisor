from django.conf import settings
from django.db import models
from django.utils import timezone


class UserSubscription(models.Model):
    """
    One current row per user (spec §4.4 Billing). Built in Milestone 1 as
    schema only; lifecycle logic lands in Milestone 8, and the spec flags
    billing for its own design pass before IAP integration.

    on_delete=PROTECT everywhere: billing records must survive account
    deletion (§5 anonymize-and-retain) — deletion scrubs the User row, it
    never removes it, and the DB refuses a hard delete that would orphan
    billing history.
    """

    class Source(models.TextChoices):
        APP_TRIAL = "app_trial"
        GOOGLE_PLAY = "google_play"
        APPLE_APP_STORE = "apple_app_store"
        ADMIN_GRANT = "admin_grant"
        TESTER_GRANT = "tester_grant"

    class State(models.TextChoices):
        TRIALING = "trialing"
        ACTIVE = "active"
        GRACE_PERIOD = "grace_period"
        EXPIRED = "expired"
        CANCELED = "canceled"
        INDEFINITE = "indefinite"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="subscription"
    )
    source = models.CharField(max_length=20, choices=Source.choices)
    state = models.CharField(max_length=20, choices=State.choices)
    google_purchase_token = models.TextField(null=True, blank=True)
    apple_original_transaction_id = models.CharField(max_length=255, null=True, blank=True)
    trial_started_at = models.DateTimeField(null=True, blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    # null = no expiry (used for `indefinite` and open-ended admin grants)
    current_period_end = models.DateTimeField(null=True, blank=True)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscriptions_granted",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def has_access(self) -> bool:
        """
        Resolve state + the relevant expiry into a single yes/no (spec §4.4).
        `canceled` keeps access until current_period_end — store semantics:
        the user paid through the period even after turning off renewal.
        """
        now = timezone.now()
        if self.state == self.State.INDEFINITE:
            return True
        if self.state == self.State.TRIALING:
            return self.trial_ends_at is not None and now < self.trial_ends_at
        if self.state in (self.State.ACTIVE, self.State.GRACE_PERIOD):
            return self.current_period_end is None or now < self.current_period_end
        if self.state == self.State.CANCELED:
            return self.current_period_end is not None and now < self.current_period_end
        return False  # expired

    def __str__(self):
        return f"{self.user}: {self.source}/{self.state}"


class SubscriptionEvent(models.Model):
    """
    Append-only audit log (spec §4.4): webhook handlers and manual grants
    write here *before* touching UserSubscription, protecting against
    out-of-order/duplicate webhook deliveries silently corrupting state.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="subscription_events"
    )
    source = models.CharField(max_length=20, choices=UserSubscription.Source.choices)
    event_type = models.CharField(max_length=100)
    # Full RTDN/ASSN webhook JSON, or a description of a manual grant.
    raw_payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user}: {self.event_type} ({self.source})"
