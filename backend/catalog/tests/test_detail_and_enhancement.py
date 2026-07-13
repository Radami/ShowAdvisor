"""
The provider-boundary orchestration: ensure_show_detail gating, TMDB
enhancement (ID claiming included), ensure_movie_detail, and the Tier 3
on-demand fetches. Provider clients are mocked at the sync-module seam.
"""

from unittest import mock

import pytest
from django.utils import timezone

from catalog.models import Movie, Show, TMDBShowCache
from catalog.providers import TVmazeNotFound
from catalog.sync import (
    ON_DEMAND_FETCH_LIMIT,
    _claim_show_tmdb_id,
    enhance_show_from_tmdb,
    ensure_movie_detail,
    ensure_show_detail,
    fetch_movies_on_demand,
    fetch_shows_on_demand,
    upsert_movie_from_tmdb,
    upsert_show_from_tvmaze,
)

from .payloads import (
    tmdb_movie,
    tmdb_movie_search_hit,
    tmdb_tv,
    tvmaze_show,
    tvmaze_show_full,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def tmdb_client(monkeypatch):
    client = mock.MagicMock()
    client.is_configured = True
    monkeypatch.setattr("catalog.sync.TMDBClient", mock.MagicMock(return_value=client))
    return client


@pytest.fixture
def tvmaze_client(monkeypatch):
    client = mock.MagicMock()
    monkeypatch.setattr("catalog.sync.TVmazeClient", mock.MagicMock(return_value=client))
    return client


class TestClaimShowTmdbId:
    def test_claims_free_id(self):
        show = Show.objects.create(primary_title="A", tvmaze_id=1)
        assert _claim_show_tmdb_id(show, 42) is True
        assert Show.objects.get(pk=show.pk).tmdb_id == 42

    def test_refuses_id_owned_by_another_show(self):
        Show.objects.create(primary_title="Owner", tvmaze_id=1, tmdb_id=42)
        show = Show.objects.create(primary_title="B", tvmaze_id=2)

        assert _claim_show_tmdb_id(show, 42) is False
        show.refresh_from_db()
        assert show.tmdb_id is None  # both DB and in-memory state restored


class TestEnsureShowDetail:
    def test_stub_show_triggers_full_fetch(self, monkeypatch):
        fetch = mock.MagicMock(side_effect=lambda s: s)
        monkeypatch.setattr("catalog.sync.fetch_show_full", fetch)
        show = upsert_show_from_tvmaze(tvmaze_show())  # no _embedded

        ensure_show_detail(show)

        fetch.assert_called_once_with(show)

    def test_full_snapshot_skips_fetch_even_with_zero_episodes(self, monkeypatch):
        fetch = mock.MagicMock()
        enhance = mock.MagicMock()
        monkeypatch.setattr("catalog.sync.fetch_show_full", fetch)
        monkeypatch.setattr("catalog.sync.enhance_show_from_tmdb", enhance)

        # A just-announced show: full detail fetched, but no episodes exist.
        payload = tvmaze_show(_embedded={"seasons": [], "episodes": []})
        show = upsert_show_from_tvmaze(payload)

        ensure_show_detail(show)

        fetch.assert_not_called()
        enhance.assert_called_once()  # opportunistic TMDB pass still runs

    def test_fully_synced_show_makes_no_provider_calls(self, monkeypatch):
        fetch = mock.MagicMock()
        enhance = mock.MagicMock()
        monkeypatch.setattr("catalog.sync.fetch_show_full", fetch)
        monkeypatch.setattr("catalog.sync.enhance_show_from_tmdb", enhance)

        show = upsert_show_from_tvmaze(tvmaze_show_full())
        TMDBShowCache.objects.create(show=show, data=tmdb_tv(), fetched_at=timezone.now())
        show = Show.objects.get(pk=show.pk)

        ensure_show_detail(show)

        fetch.assert_not_called()
        enhance.assert_not_called()

    def test_fetch_failure_is_swallowed(self, monkeypatch):
        monkeypatch.setattr(
            "catalog.sync.fetch_show_full", mock.MagicMock(side_effect=RuntimeError)
        )
        show = upsert_show_from_tvmaze(tvmaze_show())
        assert ensure_show_detail(show) is show  # degrades, never raises


class TestEnhanceShowFromTmdb:
    def test_resolves_via_imdb_claims_id_and_caches(self, tmdb_client):
        show = upsert_show_from_tvmaze(tvmaze_show())
        tmdb_client.find_by_imdb_id.return_value = {"tv_results": [{"id": 61217}]}
        tmdb_client.tv_details.return_value = tmdb_tv()

        enhance_show_from_tmdb(show)

        tmdb_client.find_by_imdb_id.assert_called_once_with("tt3544772")
        assert Show.objects.get(pk=show.pk).tmdb_id == 61217
        assert TMDBShowCache.objects.filter(show=show).exists()
        assert show.alternate_titles.filter(title="Kirby et ses potes").exists()

    def test_id_owned_by_other_show_aborts_before_fetching(self, tmdb_client):
        Show.objects.create(primary_title="Owner", tvmaze_id=1, tmdb_id=61217)
        show = upsert_show_from_tvmaze(tvmaze_show())
        tmdb_client.find_by_imdb_id.return_value = {"tv_results": [{"id": 61217}]}

        enhance_show_from_tmdb(show)

        # Neither the other record's payload fetched nor cached on this show.
        tmdb_client.tv_details.assert_not_called()
        assert not TMDBShowCache.objects.filter(show=show).exists()
        assert Show.objects.get(pk=show.pk).tmdb_id is None

    def test_unconfigured_client_is_a_noop(self, tmdb_client):
        tmdb_client.is_configured = False
        show = upsert_show_from_tvmaze(tvmaze_show())

        enhance_show_from_tmdb(show)

        tmdb_client.find_by_imdb_id.assert_not_called()

    def test_no_imdb_id_is_a_noop(self, tmdb_client):
        show = upsert_show_from_tvmaze(tvmaze_show(externals={}))

        enhance_show_from_tmdb(show)

        tmdb_client.find_by_imdb_id.assert_not_called()
        assert Show.objects.get(pk=show.pk).tmdb_id is None

    def test_provider_error_is_swallowed(self, tmdb_client):
        show = upsert_show_from_tvmaze(tvmaze_show())
        tmdb_client.find_by_imdb_id.side_effect = RuntimeError

        assert enhance_show_from_tmdb(show) is show


class TestEnsureMovieDetail:
    def test_full_snapshot_skips_provider_entirely(self, tmdb_client):
        movie = upsert_movie_from_tmdb(tmdb_movie())

        ensure_movie_detail(movie)

        tmdb_client.movie_details.assert_not_called()

    def test_stub_movie_fetches_full_detail(self, tmdb_client):
        movie = upsert_movie_from_tmdb(tmdb_movie_search_hit())
        tmdb_client.movie_details.return_value = tmdb_movie()

        movie = ensure_movie_detail(movie)

        assert movie.runtime == 167

    def test_fetch_failure_returns_stub(self, tmdb_client):
        movie = upsert_movie_from_tmdb(tmdb_movie_search_hit())
        tmdb_client.movie_details.side_effect = RuntimeError

        assert ensure_movie_detail(movie).runtime is None


class TestOnDemandFetch:
    def test_show_hits_upserted_with_akas(self, tvmaze_client):
        tvmaze_client.search_shows.return_value = [
            {"score": 0.9, "show": tvmaze_show(tvmaze_id=400, name="Money Heist")}
        ]
        tvmaze_client.show_akas.return_value = [
            {"name": "La Casa de Papel", "country": {"code": "ES"}}
        ]

        fetch_shows_on_demand("la casa de papel")

        # The AKA is what lets the local re-query match the user's alias.
        show = Show.objects.get(tvmaze_id=400)
        assert show.alternate_titles.filter(title="La Casa de Papel").exists()

    def test_missing_akas_do_not_fail_the_fetch(self, tvmaze_client):
        tvmaze_client.search_shows.return_value = [
            {"score": 0.9, "show": tvmaze_show(tvmaze_id=401)}
        ]
        tvmaze_client.show_akas.side_effect = TVmazeNotFound("/shows/401/akas")

        fetch_shows_on_demand("kirby")

        assert Show.objects.filter(tvmaze_id=401).exists()

    def test_provider_failure_degrades_silently(self, tvmaze_client):
        tvmaze_client.search_shows.side_effect = RuntimeError

        fetch_shows_on_demand("anything")  # must not raise

        assert not Show.objects.exists()

    def test_movie_hits_upserted_up_to_limit(self, tmdb_client):
        hits = [
            tmdb_movie_search_hit(tmdb_id=1000 + i) for i in range(ON_DEMAND_FETCH_LIMIT + 5)
        ]
        tmdb_client.search_movies.return_value = {"results": hits}

        fetch_movies_on_demand("dune")

        assert Movie.objects.count() == ON_DEMAND_FETCH_LIMIT

    def test_unconfigured_tmdb_skips_movie_fetch(self, tmdb_client):
        tmdb_client.is_configured = False

        fetch_movies_on_demand("dune")

        tmdb_client.search_movies.assert_not_called()
