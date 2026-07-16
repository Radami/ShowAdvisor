"""Watch History (spec §3.1): merged episode+movie stream, newest first."""

import datetime

import pytest
from django.utils import timezone
from rest_framework import status

from tracking.models import WatchedEpisode, WatchedMovie

from .factories import make_episode, make_movie, make_season, make_show

pytestmark = pytest.mark.django_db


@pytest.fixture
def history(user):
    """One movie between two episodes: E2 (newest), movie, E1 (oldest)."""
    season = make_season(make_show("History Show"))
    now = timezone.now()

    def days_ago(days):
        return now - datetime.timedelta(days=days)

    WatchedEpisode.objects.create(
        user=user, episode=make_episode(season, 1), watched_at=days_ago(3)
    )
    WatchedMovie.objects.create(
        user=user, movie=make_movie("History Movie"), watched_at=days_ago(2)
    )
    WatchedEpisode.objects.create(
        user=user, episode=make_episode(season, 2), watched_at=days_ago(1)
    )


class TestWatchHistory:
    def test_merged_stream_newest_first(self, api_client, history):
        items = api_client.get("/api/history/").data["history"]

        assert [item["type"] for item in items] == ["episode", "movie", "episode"]
        assert items[0]["episode_number"] == 2
        assert items[1]["title"] == "History Movie"

    def test_episode_items_carry_show_context(self, api_client, history):
        item = api_client.get("/api/history/").data["history"][0]

        assert item["show_title"] == "History Show"
        assert item["season_number"] == 1
        assert {"show_id", "episode_id", "watched_at", "title"} <= set(item)

    def test_limit_applies_across_both_types(self, api_client, history):
        items = api_client.get("/api/history/", {"limit": 2}).data["history"]

        assert [item["type"] for item in items] == ["episode", "movie"]

    @pytest.mark.parametrize("limit", ["-1", "0"])
    def test_non_positive_limit_returns_empty_not_500(self, api_client, history, limit):
        response = api_client.get("/api/history/", {"limit": limit})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["history"] == []

    def test_non_numeric_limit_rejected(self, api_client):
        response = api_client.get("/api/history/", {"limit": "many"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_oversized_limit_is_clamped_not_rejected(self, api_client, history):
        response = api_client.get("/api/history/", {"limit": "999999"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["history"]) == 3
