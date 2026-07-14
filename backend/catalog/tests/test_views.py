"""
Search + detail endpoints (spec §3.1, §4.6). Provider work is patched at the
view seam — these tests cover HTTP contract, fallback gating and serializer
shape, not the sync internals (covered elsewhere).
"""

from unittest import mock

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import Movie, Show
from catalog.sync import TMDBPayloadKind, upsert_movie_from_tmdb, upsert_show_from_tvmaze
from tracking.models import ShowSubscription, WatchedEpisode, WatchedMovie

from .payloads import tmdb_movie, tvmaze_show, tvmaze_show_full

pytestmark = pytest.mark.django_db


@pytest.fixture
def show_fetch(monkeypatch):
    fetch = mock.MagicMock()
    monkeypatch.setattr("catalog.views.fetch_shows_on_demand", fetch)
    return fetch


@pytest.fixture
def movie_fetch(monkeypatch):
    fetch = mock.MagicMock()
    monkeypatch.setattr("catalog.views.fetch_movies_on_demand", fetch)
    return fetch


class TestSearchView:
    def test_requires_authentication(self, db):
        response = APIClient().get("/api/search/", {"q": "dune"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_query_is_rejected(self, api_client):
        assert api_client.get("/api/search/").status_code == status.HTTP_400_BAD_REQUEST

    def test_non_numeric_year_is_rejected(self, api_client):
        response = api_client.get("/api/search/", {"q": "dune", "year": "MMXX"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_local_show_hit_still_fetches_movies(self, api_client, show_fetch, movie_fetch):
        upsert_show_from_tvmaze(tvmaze_show(name="Dune"))

        response = api_client.get("/api/search/", {"q": "Dune"})

        # Per-medium fallback: the show matched locally, so no show fetch —
        # but that must not suppress the movie-side Tier 3 fetch.
        show_fetch.assert_not_called()
        movie_fetch.assert_called_once()
        assert response.data["results"][0]["title"] == "Dune"

    def test_local_movie_hit_still_fetches_shows(self, api_client, show_fetch, movie_fetch):
        upsert_movie_from_tmdb(tmdb_movie(title="Dune"), TMDBPayloadKind.DETAIL)

        api_client.get("/api/search/", {"q": "Dune"})

        movie_fetch.assert_not_called()
        show_fetch.assert_called_once()

    def test_full_miss_fetches_both_and_requeries(self, api_client, show_fetch, movie_fetch):
        show_fetch.side_effect = lambda q: upsert_show_from_tvmaze(tvmaze_show(name="Dune"))
        movie_fetch.side_effect = lambda q, y: upsert_movie_from_tmdb(
            tmdb_movie(title="Dune: Part Two"), TMDBPayloadKind.DETAIL
        )

        response = api_client.get("/api/search/", {"q": "Dune"})

        titles = {result["title"] for result in response.data["results"]}
        assert titles == {"Dune", "Dune: Part Two"}

    def test_results_interleaved_by_similarity(self, api_client, show_fetch, movie_fetch):
        upsert_show_from_tvmaze(tvmaze_show(name="Dune"))
        upsert_movie_from_tmdb(tmdb_movie(title="Dune: Part Two"), TMDBPayloadKind.DETAIL)

        results = api_client.get("/api/search/", {"q": "Dune"}).data["results"]

        # The exact-match show outranks the partial-match movie.
        assert [r["type"] for r in results] == ["show", "movie"]

    def test_show_result_shape(self, api_client, show_fetch, movie_fetch):
        upsert_show_from_tvmaze(tvmaze_show(name="Dune"))

        result = api_client.get("/api/search/", {"q": "Dune"}).data["results"][0]

        assert set(result) == {"type", "id", "title", "year", "status", "poster_url"}
        assert result["year"] == 2014  # derived from premiered


class TestShowDetailView:
    @pytest.fixture(autouse=True)
    def no_provider_calls(self, monkeypatch):
        monkeypatch.setattr("catalog.views.ensure_show_detail", lambda show: show)

    def test_detail_payload(self, api_client, user):
        show = upsert_show_from_tvmaze(tvmaze_show_full())
        ShowSubscription.objects.create(user=user, show=show)
        pilot = show.seasons.get().episodes.get(episode_number=1)
        WatchedEpisode.objects.create(user=user, episode=pilot)

        data = api_client.get(f"/api/shows/{show.pk}/").data

        assert data["title"] == "Kirby Buckets"
        assert data["subscription"] == {"status": "active"}
        episodes = {e["episode_number"]: e for e in data["seasons"][0]["episodes"]}
        assert episodes[1]["watched"] is True
        assert episodes[2]["watched"] is False

    def test_unknown_show_404s(self, api_client):
        assert api_client.get("/api/shows/12345/").status_code == status.HTTP_404_NOT_FOUND


class TestMovieDetailView:
    @pytest.fixture(autouse=True)
    def no_provider_calls(self, monkeypatch):
        monkeypatch.setattr("catalog.views.ensure_movie_detail", lambda movie: movie)

    def test_detail_payload(self, api_client, user):
        movie = upsert_movie_from_tmdb(tmdb_movie(), TMDBPayloadKind.DETAIL)
        WatchedMovie.objects.create(user=user, movie=movie)

        data = api_client.get(f"/api/movies/{movie.pk}/").data

        assert data["title"] == "Dune: Part Two"
        assert data["watched"] is True
        assert data["subscription"] is None
        assert data["poster_url"] == "https://image.tmdb.org/t/p/w342/dune2.jpg"

    def test_unknown_movie_404s(self, api_client):
        assert api_client.get("/api/movies/12345/").status_code == status.HTTP_404_NOT_FOUND
