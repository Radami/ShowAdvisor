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
    list_display = ("user", "episode", "watched", "watched_at")
    list_filter = ("watched",)
    search_fields = ("user__username", "episode__title", "episode__season__show__title")


@admin.register(WatchedMovie)
class WatchedMovieAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "watched", "watched_at")
    list_filter = ("watched",)
    search_fields = ("user__username", "movie__title")


@admin.register(ShowSubscription)
class ShowSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "show", "created_at")
    search_fields = ("user__username", "show__title")


@admin.register(MovieSubscription)
class MovieSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "created_at")
    search_fields = ("user__username", "movie__title")


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("user", "show", "movie", "value", "updated_at")
    search_fields = ("user__username", "show__title", "movie__title")
