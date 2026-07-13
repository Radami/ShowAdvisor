"""upsert_movie_from_tmdb: snapshot overwrite + the partial-payload guard."""

import datetime

import pytest

from catalog.models import Movie
from catalog.sync import _cache_data, upsert_movie_from_tmdb

from .payloads import tmdb_movie, tmdb_movie_search_hit

pytestmark = pytest.mark.django_db


class TestMovieUpsert:
    def test_creates_movie_from_search_hit(self):
        movie = upsert_movie_from_tmdb(tmdb_movie_search_hit())

        assert movie.tmdb_id == 693134
        assert movie.primary_title == "Dune: Part Two"
        assert movie.release_date == datetime.date(2024, 2, 27)
        assert movie.runtime is None  # search hits are partial

    def test_full_detail_fills_runtime_and_akas(self):
        upsert_movie_from_tmdb(tmdb_movie_search_hit())
        movie = upsert_movie_from_tmdb(tmdb_movie())

        assert Movie.objects.count() == 1
        assert movie.runtime == 167
        assert movie.alternate_titles.filter(
            title="Dune: Parte dos", country="ES"
        ).exists()

    def test_search_hit_never_clobbers_full_snapshot(self):
        upsert_movie_from_tmdb(tmdb_movie())
        movie = upsert_movie_from_tmdb(
            tmdb_movie_search_hit(title="Stale Localized Title")
        )

        # The partial payload is dropped: snapshot, fetched_at and the
        # canonical record all keep the full-detail data.
        assert "runtime" in _cache_data(movie, "tmdb_cache")
        assert movie.primary_title == "Dune: Part Two"
        assert movie.runtime == 167

    def test_full_detail_reupsert_updates_in_place(self):
        upsert_movie_from_tmdb(tmdb_movie())
        movie = upsert_movie_from_tmdb(tmdb_movie(runtime=170))

        assert Movie.objects.count() == 1
        assert movie.runtime == 170

    def test_aka_sync_is_idempotent_and_skips_primary_title(self):
        payload = tmdb_movie(
            alternative_titles={
                "titles": [
                    {"iso_3166_1": "ES", "title": "Dune: Parte dos"},
                    {"iso_3166_1": "US", "title": "Dune: Part Two"},  # == primary
                ]
            }
        )
        upsert_movie_from_tmdb(payload)
        movie = upsert_movie_from_tmdb(payload)

        assert movie.alternate_titles.count() == 1
        assert movie.alternate_titles.get().title == "Dune: Parte dos"
