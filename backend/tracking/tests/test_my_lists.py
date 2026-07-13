"""
The Watch list / Up next / Paused buckets (spec §3.1, task 5.3) — the rules
these encode: watch list keeps a show until *everything* is watched, up next
needs unaired episodes, paused trumps both; watched movies vanish entirely.
"""

import pytest
from rest_framework import status

from tracking.models import (
    MovieSubscription,
    ShowSubscription,
    SubscriptionStatus,
    WatchedEpisode,
    WatchedMovie,
)

from .factories import make_episode, make_movie, make_season, make_show

pytestmark = pytest.mark.django_db


def _subscribe_show(user, show, sub_status=SubscriptionStatus.ACTIVE):
    return ShowSubscription.objects.create(user=user, show=show, status=sub_status)


def _titles(bucket):
    return {item["title"] for item in bucket}


class TestMyShows:
    def test_partially_watched_running_show(self, api_client, user):
        show = make_show("Running Show")
        season = make_season(show)
        watched = make_episode(season, 1, airs_in_days=-14)
        make_episode(season, 2, airs_in_days=-7)  # aired, unwatched
        make_episode(season, 3, airs_in_days=7)  # upcoming
        WatchedEpisode.objects.create(user=user, episode=watched)
        _subscribe_show(user, show)

        data = api_client.get("/api/my/shows/").data

        assert _titles(data["watch_list"]) == {"Running Show"}
        assert _titles(data["up_next"]) == {"Running Show"}
        item = data["watch_list"][0]
        assert item["unwatched_count"] == 1  # aired-unwatched only
        assert item["next_airstamp"] is not None
        assert item["subscription_status"] == SubscriptionStatus.ACTIVE

    def test_fully_watched_ended_show_leaves_both_buckets(self, api_client, user):
        show = make_show("Finished Show")
        season = make_season(show)
        for number in (1, 2):
            episode = make_episode(season, number, airs_in_days=-30)
            WatchedEpisode.objects.create(user=user, episode=episode)
        _subscribe_show(user, show)

        data = api_client.get("/api/my/shows/").data

        assert data["watch_list"] == []
        assert data["up_next"] == []

    def test_caught_up_show_with_upcoming_episode_stays(self, api_client, user):
        show = make_show("Caught Up")
        season = make_season(show)
        episode = make_episode(season, 1, airs_in_days=-7)
        make_episode(season, 2, airs_in_days=7)
        WatchedEpisode.objects.create(user=user, episode=episode)
        _subscribe_show(user, show)

        data = api_client.get("/api/my/shows/").data

        # Unwatched (unaired) episodes exist, so it stays on the watch list
        # and is up next; but nothing aired is unwatched.
        assert _titles(data["watch_list"]) == {"Caught Up"}
        assert _titles(data["up_next"]) == {"Caught Up"}
        assert data["watch_list"][0]["unwatched_count"] == 0

    def test_show_without_synced_episodes_stays_on_watch_list(self, api_client, user):
        _subscribe_show(user, make_show("Fresh Stub"))

        data = api_client.get("/api/my/shows/").data

        assert _titles(data["watch_list"]) == {"Fresh Stub"}
        assert data["up_next"] == []

    def test_paused_show_only_in_paused_bucket(self, api_client, user):
        show = make_show("Paused Show")
        season = make_season(show)
        make_episode(season, 1, airs_in_days=-7)
        _subscribe_show(user, show, SubscriptionStatus.PAUSED)

        data = api_client.get("/api/my/shows/").data

        assert data["watch_list"] == []
        assert data["up_next"] == []
        assert _titles(data["paused"]) == {"Paused Show"}

    def test_other_users_subscriptions_invisible(self, api_client, user, django_user_model):
        other = django_user_model.objects.create_user(username="o", email="o@example.com")
        _subscribe_show(other, make_show("Not Mine"))

        data = api_client.get("/api/my/shows/").data

        assert data == {"watch_list": [], "up_next": [], "paused": []}


class TestMyMovies:
    def _subscribe(self, user, movie, sub_status=SubscriptionStatus.ACTIVE):
        return MovieSubscription.objects.create(user=user, movie=movie, status=sub_status)

    def test_released_unwatched_only_on_watch_list(self, api_client, user):
        self._subscribe(user, make_movie("Released", releases_in_days=-30))

        data = api_client.get("/api/my/movies/").data

        assert _titles(data["watch_list"]) == {"Released"}
        assert data["up_next"] == []

    def test_unreleased_in_both_buckets(self, api_client, user):
        self._subscribe(user, make_movie("Upcoming", releases_in_days=30))
        self._subscribe(user, make_movie("Undated", releases_in_days=None))

        data = api_client.get("/api/my/movies/").data

        assert _titles(data["watch_list"]) == {"Upcoming", "Undated"}
        assert _titles(data["up_next"]) == {"Upcoming", "Undated"}

    def test_watched_movie_drops_out_entirely(self, api_client, user):
        released = make_movie("Watched Released", releases_in_days=-30)
        upcoming = make_movie("Watched Early", releases_in_days=30)  # e.g. festival
        for movie in (released, upcoming):
            self._subscribe(user, movie)
            WatchedMovie.objects.create(user=user, movie=movie)

        data = api_client.get("/api/my/movies/").data

        # Watched means gone from both buckets — history only (§3.1) — even
        # for a movie watched before its wide release date.
        assert data["watch_list"] == []
        assert data["up_next"] == []

    def test_paused_movie_only_in_paused_bucket(self, api_client, user):
        self._subscribe(
            user, make_movie("Paused", releases_in_days=30), SubscriptionStatus.PAUSED
        )

        data = api_client.get("/api/my/movies/").data

        assert data["watch_list"] == []
        assert data["up_next"] == []
        assert _titles(data["paused"]) == {"Paused"}
