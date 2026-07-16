"""
Own-DB trigram search (spec §4.6) against real Postgres/pg_trgm — these
tests are why the suite can't run on SQLite. Similarity values asserted
around were measured with pg_trgm's similarity() directly.
"""

import datetime
import itertools

import pytest

from catalog.models import AlternateMovieTitle, AlternateShowTitle, Movie, Show
from catalog.search import MAX_RESULTS, search_movies, search_shows

pytestmark = pytest.mark.django_db

_ids = itertools.count(10_000)


def make_show(title, premiered=None):
    return Show.objects.create(primary_title=title, tvmaze_id=next(_ids), premiered=premiered)


def make_movie(title, release_date=None):
    return Movie.objects.create(primary_title=title, tmdb_id=next(_ids), release_date=release_date)


class TestSearchShows:
    def test_exact_match_ranks_first(self):
        make_show("Breaking In")
        exact = make_show("Breaking Bad")

        results = search_shows("Breaking Bad")

        assert results[0].pk == exact.pk
        assert results[0].similarity == pytest.approx(1.0)

    def test_typo_still_matches(self):
        show = make_show("Breaking Bad")

        results = search_shows("Braking Bad")

        assert [s.pk for s in results] == [show.pk]

    def test_short_substring_rescued_by_icontains(self):
        # similarity('Star Trek: The Next Generation', 'Trek') ≈ 0.17 — under
        # the 0.3 cutoff; the icontains OR keeps strict substrings matching.
        show = make_show("Star Trek: The Next Generation")
        make_show("Breaking Bad")  # noise: neither similar nor a substring hit

        results = search_shows("Trek")

        assert [s.pk for s in results] == [show.pk]

    def test_alternate_title_matches(self):
        show = make_show("Money Heist")
        AlternateShowTitle.objects.create(show=show, title="La Casa de Papel", country="ES")

        results = search_shows("La Casa de Papel")

        assert [s.pk for s in results] == [show.pk]

    def test_year_filters_on_premiere(self):
        make_show("The Office", premiered=datetime.date(2001, 7, 9))
        us_version = make_show("The Office", premiered=datetime.date(2005, 3, 24))

        assert len(search_shows("The Office")) == 2
        assert [s.pk for s in search_shows("The Office", year="2005")] == [us_version.pk]

    def test_results_capped(self):
        for i in range(MAX_RESULTS + 5):
            make_show(f"Generic Show {i}")

        assert len(search_shows("Generic Show")) == MAX_RESULTS

    def test_no_match_returns_empty(self):
        make_show("Breaking Bad")
        assert search_shows("Succession") == []


class TestSearchMovies:
    def test_typo_and_year_filter_combine(self):
        remake = make_movie("Oppenheimer", release_date=datetime.date(2023, 7, 21))
        make_movie("Oppenheimer", release_date=datetime.date(1980, 1, 1))

        results = search_movies("Openheimer", year="2023")

        assert [m.pk for m in results] == [remake.pk]

    def test_alternate_title_matches(self):
        movie = make_movie("Dune: Part Two")
        AlternateMovieTitle.objects.create(movie=movie, title="Dune: Parte dos", country="ES")

        results = search_movies("Dune Parte dos")

        assert [m.pk for m in results] == [movie.pk]
