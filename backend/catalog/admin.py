from django.contrib import admin

from .models import (
    Episode,
    Movie,
    MovieTitle,
    Season,
    Show,
    ShowTitle,
    TMDBMovieCache,
    TMDBShowCache,
    TVmazeShowCache,
)


class ShowTitleInline(admin.TabularInline):
    model = ShowTitle
    extra = 0


class SeasonInline(admin.TabularInline):
    model = Season
    extra = 0


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "premiered", "network", "tvmaze_id", "tmdb_id")
    list_filter = ("status",)
    search_fields = ("title", "titles__title", "tvmaze_id", "tmdb_id")
    readonly_fields = ("created_at", "updated_at")
    inlines = [ShowTitleInline, SeasonInline]


class EpisodeInline(admin.TabularInline):
    model = Episode
    extra = 0


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("show", "season_number", "tvmaze_id")
    search_fields = ("show__title",)
    inlines = [EpisodeInline]


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = ("__str__", "air_date", "runtime", "tvmaze_id")
    search_fields = ("title", "season__show__title")
    list_filter = ("air_date",)


class MovieTitleInline(admin.TabularInline):
    model = MovieTitle
    extra = 0


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "release_date", "runtime", "tmdb_id")
    search_fields = ("title", "titles__title", "tmdb_id")
    readonly_fields = ("created_at", "updated_at")
    inlines = [MovieTitleInline]


@admin.register(ShowTitle)
class ShowTitleAdmin(admin.ModelAdmin):
    list_display = ("title", "show", "language", "country", "is_primary")
    list_filter = ("language", "is_primary")
    search_fields = ("title", "show__title")


@admin.register(MovieTitle)
class MovieTitleAdmin(admin.ModelAdmin):
    list_display = ("title", "movie", "language", "country", "is_primary")
    list_filter = ("language", "is_primary")
    search_fields = ("title", "movie__title")


@admin.register(TVmazeShowCache)
class TVmazeShowCacheAdmin(admin.ModelAdmin):
    list_display = ("show", "fetched_at")
    search_fields = ("show__title",)


@admin.register(TMDBShowCache)
class TMDBShowCacheAdmin(admin.ModelAdmin):
    list_display = ("show", "fetched_at")
    search_fields = ("show__title",)


@admin.register(TMDBMovieCache)
class TMDBMovieCacheAdmin(admin.ModelAdmin):
    list_display = ("movie", "fetched_at")
    search_fields = ("movie__title",)
