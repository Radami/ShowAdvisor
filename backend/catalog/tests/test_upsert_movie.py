"""upsert_movie_from_tmdb: snapshot overwrite + the partial-payload guard."""

import datetime

import pytest

from catalog.models import Movie
from catalog.sync import TMDBPayloadKind, upsert_movie_from_tmdb

from .payloads import tmdb_movie, tmdb_movie_search_hit

pytestmark = pytest.mark.django_db


class TestMovieUpsert:
    def test_creates_movie_from_search_hit(self):
        movie = upsert_movie_from_tmdb(tmdb_movie_search_hit(), TMDBPayloadKind.SEARCH_HIT)

        assert movie.tmdb_id == 693134
        assert movie.primary_title == "Dune: Part Two"
        assert movie.release_date == datetime.date(2024, 2, 27)
        assert movie.runtime is None  # search hits are partial
        assert not movie.tmdb_cache.is_detail

    def test_full_detail_fills_runtime_and_akas(self):
        upsert_movie_from_tmdb(tmdb_movie_search_hit(), TMDBPayloadKind.SEARCH_HIT)
        movie = upsert_movie_from_tmdb(tmdb_movie(), TMDBPayloadKind.DETAIL)

        assert Movie.objects.count() == 1
        assert movie.runtime == 167
        assert movie.alternate_titles.filter(
            title="Dune: Parte dos", country="ES"
        ).exists()

    def test_search_hit_never_clobbers_full_snapshot(self):
        upsert_movie_from_tmdb(tmdb_movie(), TMDBPayloadKind.DETAIL)
        movie = upsert_movie_from_tmdb(
            tmdb_movie_search_hit(title="Stale Localized Title"),
            TMDBPayloadKind.SEARCH_HIT,
        )

        # The partial payload is dropped: snapshot, fetched_at and the
        # canonical record all keep the full-detail data.
        assert movie.tmdb_cache.is_detail
        assert movie.primary_title == "Dune: Part Two"
        assert movie.runtime == 167

    def test_full_detail_reupsert_updates_in_place(self):
        upsert_movie_from_tmdb(tmdb_movie(), TMDBPayloadKind.DETAIL)
        movie = upsert_movie_from_tmdb(tmdb_movie(runtime=170), TMDBPayloadKind.DETAIL)

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
        upsert_movie_from_tmdb(payload, TMDBPayloadKind.DETAIL)
        movie = upsert_movie_from_tmdb(payload, TMDBPayloadKind.DETAIL)

        assert movie.alternate_titles.count() == 1
        assert movie.alternate_titles.get().title == "Dune: Parte dos"
