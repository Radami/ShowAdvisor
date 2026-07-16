from rest_framework import serializers

from .images import movie_poster_url, show_poster_url
from .models import Episode, Movie, Season, Show


class ShowSearchResultSerializer(serializers.ModelSerializer):
    type = serializers.ReadOnlyField(default="show")
    title = serializers.CharField(source="primary_title")
    year = serializers.SerializerMethodField()
    poster_url = serializers.SerializerMethodField()

    class Meta:
        model = Show
        fields = ["type", "id", "title", "year", "status", "poster_url"]

    def get_year(self, show):
        return show.premiered.year if show.premiered else None

    def get_poster_url(self, show):
        return show_poster_url(show)


class MovieSearchResultSerializer(serializers.ModelSerializer):
    type = serializers.ReadOnlyField(default="movie")
    title = serializers.CharField(source="primary_title")
    year = serializers.SerializerMethodField()
    poster_url = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = ["type", "id", "title", "year", "release_date", "poster_url"]

    def get_year(self, movie):
        return movie.release_date.year if movie.release_date else None

    def get_poster_url(self, movie):
        return movie_poster_url(movie)


class EpisodeSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="primary_title")
    watched = serializers.SerializerMethodField()

    class Meta:
        model = Episode
        fields = [
            "id",
            "episode_number",
            "title",
            "overview",
            "air_date",
            "airstamp",
            "runtime",
            "watched",
        ]

    def get_watched(self, episode):
        return episode.id in self.context.get("watched_episode_ids", ())


class SeasonSerializer(serializers.ModelSerializer):
    episodes = EpisodeSerializer(many=True)

    class Meta:
        model = Season
        fields = ["id", "season_number", "episodes"]


class ShowDetailSerializer(serializers.ModelSerializer):
    """Backs the Show detail screen (spec §3.1): header info + season/episode list."""

    title = serializers.CharField(source="primary_title")
    poster_url = serializers.SerializerMethodField()
    subscription = serializers.SerializerMethodField()
    seasons = SeasonSerializer(many=True)

    class Meta:
        model = Show
        fields = [
            "id",
            "title",
            "status",
            "premiered",
            "ended",
            "summary",
            "runtime",
            "network",
            "schedule",
            "poster_url",
            "subscription",
            "seasons",
        ]

    def get_poster_url(self, show):
        return show_poster_url(show)

    def get_subscription(self, show):
        subscription = self.context.get("subscription")
        return {"status": subscription.status} if subscription else None


class MovieDetailSerializer(serializers.ModelSerializer):
    """Backs the Movie detail screen (spec §3.1): header info + watched state."""

    title = serializers.CharField(source="primary_title")
    poster_url = serializers.SerializerMethodField()
    subscription = serializers.SerializerMethodField()
    watched = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "release_date",
            "runtime",
            "summary",
            "poster_url",
            "subscription",
            "watched",
        ]

    def get_poster_url(self, movie):
        return movie_poster_url(movie)

    def get_subscription(self, movie):
        subscription = self.context.get("subscription")
        return {"status": subscription.status} if subscription else None

    def get_watched(self, movie):
        return self.context.get("watched", False)
