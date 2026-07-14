from django.contrib import admin

from .models import (
    AlternateEpisodeTitle,
    AlternateMovieTitle,
    AlternateShowTitle,
    Episode,
    Movie,
    Season,
    Show,
    TMDBMovieCache,
    TMDBShowCache,
    TVmazeShowCache,
)


class AlternateShowTitleInline(admin.TabularInline):
    model = AlternateShowTitle
    extra = 0


class SeasonInline(admin.TabularInline):
    model = Season
    extra = 0


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ("primary_title", "status", "premiered", "network", "tvmaze_id", "tmdb_id")
    list_filter = ("status",)
    search_fields = ("primary_title", "alternate_titles__title", "tvmaze_id", "tmdb_id")
    readonly_fields = ("created_at", "updated_at")
    inlines = [AlternateShowTitleInline, SeasonInline]


class EpisodeInline(admin.TabularInline):
    model = Episode
    extra = 0


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("show", "season_number", "tvmaze_id")
    search_fields = ("show__primary_title",)
    inlines = [EpisodeInline]


class AlternateEpisodeTitleInline(admin.TabularInline):
    model = AlternateEpisodeTitle
    extra = 0


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = ("__str__", "air_date", "runtime", "tvmaze_id")
    search_fields = ("primary_title", "season__show__primary_title")
    list_filter = ("air_date",)
    inlines = [AlternateEpisodeTitleInline]


class AlternateMovieTitleInline(admin.TabularInline):
    model = AlternateMovieTitle
    extra = 0


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("primary_title", "release_date", "runtime", "tmdb_id")
    search_fields = ("primary_title", "alternate_titles__title", "tmdb_id")
    readonly_fields = ("created_at", "updated_at")
    inlines = [AlternateMovieTitleInline]


@admin.register(AlternateEpisodeTitle)
class AlternateEpisodeTitleAdmin(admin.ModelAdmin):
    list_display = ("title", "episode", "country")
    list_filter = ("country",)
    search_fields = ("title", "episode__primary_title")


@admin.register(AlternateShowTitle)
class AlternateShowTitleAdmin(admin.ModelAdmin):
    list_display = ("title", "show", "country")
    list_filter = ("country",)
    search_fields = ("title", "show__primary_title")


@admin.register(AlternateMovieTitle)
class AlternateMovieTitleAdmin(admin.ModelAdmin):
    list_display = ("title", "movie", "country")
    list_filter = ("country",)
    search_fields = ("title", "movie__primary_title")


@admin.register(TVmazeShowCache)
class TVmazeShowCacheAdmin(admin.ModelAdmin):
    list_display = ("show", "fetched_at")
    search_fields = ("show__primary_title",)


@admin.register(TMDBShowCache)
class TMDBShowCacheAdmin(admin.ModelAdmin):
    list_display = ("show", "fetched_at")
    search_fields = ("show__primary_title",)


@admin.register(TMDBMovieCache)
class TMDBMovieCacheAdmin(admin.ModelAdmin):
    list_display = ("movie", "fetched_at")
    search_fields = ("movie__primary_title",)
