from django.contrib import admin

from .models import SubscriptionEvent, UserSubscription


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "source", "state", "has_access", "trial_ends_at", "current_period_end")
    list_filter = ("source", "state")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(boolean=True)
    def has_access(self, obj):
        return obj.has_access


@admin.register(SubscriptionEvent)
class SubscriptionEventAdmin(admin.ModelAdmin):
    """Append-only: events are written by code, never edited by hand."""

    list_display = ("user", "source", "event_type", "created_at")
    list_filter = ("source",)
    search_fields = ("user__username", "event_type")
    readonly_fields = ("user", "source", "event_type", "raw_payload", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
