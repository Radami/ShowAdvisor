from django.contrib import admin

from .models import (
    MovieSubscription,
    Rating,
    ShowSubscription,
    WatchedEpisode,
    WatchedMovie,
)


@admin.register(WatchedEpisode)
class WatchedEpisodeAdmin(admin.ModelAdmin):
    list_display = ("user", "episode", "watched_at")
    search_fields = ("user__username", "episode__primary_title", "episode__season__show__primary_title")


@admin.register(WatchedMovie)
class WatchedMovieAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "watched_at")
    search_fields = ("user__username", "movie__primary_title")


@admin.register(ShowSubscription)
class ShowSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "show", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username", "show__primary_title")


@admin.register(MovieSubscription)
class MovieSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username", "movie__primary_title")


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("user", "show", "movie", "value", "updated_at")
    search_fields = ("user__username", "show__primary_title", "movie__primary_title")
