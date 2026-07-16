"""Mark watched/unwatched (task 5.1): presence semantics, idempotency."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from tracking.models import WatchedEpisode, WatchedMovie

from .factories import make_episode, make_movie, make_season, make_show

pytestmark = pytest.mark.django_db


@pytest.fixture
def season(db):
    return make_season(make_show())


class TestEpisodeWatched:
    def test_requires_authentication(self, season):
        episode = make_episode(season, 1)
        response = APIClient().post(f"/api/episodes/{episode.pk}/watched/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_is_idempotent(self, api_client, user, season):
        episode = make_episode(season, 1)

        for _ in range(2):
            response = api_client.post(f"/api/episodes/{episode.pk}/watched/")
            assert response.status_code == status.HTTP_204_NO_CONTENT

        assert WatchedEpisode.objects.filter(user=user, episode=episode).count() == 1

    def test_delete_unwatches_and_is_idempotent(self, api_client, user, season):
        episode = make_episode(season, 1)
        WatchedEpisode.objects.create(user=user, episode=episode)

        for _ in range(2):
            response = api_client.delete(f"/api/episodes/{episode.pk}/watched/")
            assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not WatchedEpisode.objects.filter(user=user).exists()

    def test_unknown_episode_404s(self, api_client):
        response = api_client.post("/api/episodes/12345/watched/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSeasonWatched:
    def test_marks_only_aired_episodes(self, api_client, user, season):
        aired = make_episode(season, 1, airs_in_days=-7)
        make_episode(season, 2, airs_in_days=7)  # upcoming
        make_episode(season, 3, airs_in_days=None)  # unscheduled

        response = api_client.post(f"/api/seasons/{season.pk}/watched/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        watched = WatchedEpisode.objects.filter(user=user)
        assert [w.episode_id for w in watched] == [aired.pk]

    def test_already_watched_episodes_are_kept(self, api_client, user, season):
        episode = make_episode(season, 1)
        make_episode(season, 2)
        original = WatchedEpisode.objects.create(user=user, episode=episode)

        api_client.post(f"/api/seasons/{season.pk}/watched/")

        assert WatchedEpisode.objects.filter(user=user).count() == 2
        assert WatchedEpisode.objects.get(episode=episode).pk == original.pk

    def test_delete_unwatches_whole_season_for_this_user_only(self, api_client, user, season):
        episode = make_episode(season, 1)
        WatchedEpisode.objects.create(user=user, episode=episode)
        other = get_user_model().objects.create_user(username="other", email="o@example.com")
        WatchedEpisode.objects.create(user=other, episode=episode)

        api_client.delete(f"/api/seasons/{season.pk}/watched/")

        assert not WatchedEpisode.objects.filter(user=user).exists()
        assert WatchedEpisode.objects.filter(user=other).exists()


class TestMovieWatched:
    def test_post_is_idempotent(self, api_client, user):
        movie = make_movie()

        for _ in range(2):
            response = api_client.post(f"/api/movies/{movie.pk}/watched/")
            assert response.status_code == status.HTTP_204_NO_CONTENT

        assert WatchedMovie.objects.filter(user=user, movie=movie).count() == 1

    def test_delete_unwatches(self, api_client, user):
        movie = make_movie()
        WatchedMovie.objects.create(user=user, movie=movie)

        api_client.delete(f"/api/movies/{movie.pk}/watched/")

        assert not WatchedMovie.objects.filter(user=user).exists()
