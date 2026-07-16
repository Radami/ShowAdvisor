"""Canonical-record merge (spec §4.7): TVmaze wins, TMDB fills gaps."""

import datetime

import pytest
from django.utils import timezone

from catalog.models import Movie, Show, TMDBMovieCache, TMDBShowCache, TVmazeShowCache
from catalog.sync import _first, recompute_movie, recompute_show, strip_html

from .payloads import tmdb_movie, tmdb_tv, tvmaze_show


class TestHelpers:
    def test_strip_html_removes_tags_and_whitespace(self):
        assert strip_html("<p>The <b>bold</b> claim.</p> ") == "The bold claim."

    def test_strip_html_tolerates_none(self):
        assert strip_html(None) == ""

    @pytest.mark.parametrize(
        ("values", "expected"),
        [
            ((None, "", "b"), "b"),
            (([], {}), None),
            ((0, "a"), 0),  # 0 is a legitimate value (e.g. runtime), not "empty"
            (("a", "b"), "a"),
            ((None, None), None),
        ],
    )
    def test_first_skips_empty_values(self, values, expected):
        assert _first(*values) == expected


def _show_with_caches(tvmaze=None, tmdb=None, tvmaze_id=1):
    show = Show.objects.create(primary_title="placeholder", tvmaze_id=tvmaze_id)
    if tvmaze is not None:
        TVmazeShowCache.objects.create(show=show, data=tvmaze, fetched_at=timezone.now())
    if tmdb is not None:
        TMDBShowCache.objects.create(show=show, data=tmdb, fetched_at=timezone.now())
    # Fresh instance so the one-to-one relation caches aren't stale.
    return Show.objects.get(pk=show.pk)


@pytest.mark.django_db
class TestRecomputeShow:
    def test_tvmaze_wins_over_tmdb(self):
        show = _show_with_caches(
            tvmaze=tvmaze_show(),
            tmdb=tmdb_tv(
                name="Wrong Name",
                status="Returning Series",
                overview="tmdb overview",
                networks=[{"name": "TMDB Net"}],
            ),
        )
        recompute_show(show)

        assert show.primary_title == "Kirby Buckets"
        assert show.status == "Ended"
        assert show.summary == "The series mixes live-action and animation."
        assert show.runtime == 30
        assert show.network == "Disney XD"
        assert show.premiered == datetime.date(2014, 10, 20)
        assert show.schedule == {"time": "07:00", "days": ["Monday"]}

    def test_tmdb_fills_tvmaze_gaps(self):
        sparse = tvmaze_show(
            name=None, status=None, runtime=None, averageRuntime=None,
            premiered=None, ended=None, summary=None, network=None,
            webChannel=None, schedule=None,
        )
        show = _show_with_caches(tvmaze=sparse, tmdb=tmdb_tv())
        recompute_show(show)

        assert show.primary_title == "Kirby Buckets"
        assert show.status == "Ended"
        assert show.summary.startswith("13-year-old Kirby")
        assert show.runtime == 22  # episode_run_time[0]
        assert show.network == "Disney XD"  # networks[0]
        assert show.premiered == datetime.date(2014, 10, 20)
        assert show.ended == datetime.date(2017, 2, 2)  # last_air_date, status Ended

    def test_tmdb_ended_only_for_finished_statuses(self):
        show = _show_with_caches(tmdb=tmdb_tv(status="Returning Series"))
        recompute_show(show)
        assert show.ended is None

    def test_web_channel_used_when_no_network(self):
        payload = tvmaze_show(network=None, webChannel={"name": "Netflix"})
        show = _show_with_caches(tvmaze=payload)
        recompute_show(show)
        assert show.network == "Netflix"

    def test_takedown_purge_recomputes_from_remaining_cache(self):
        show = _show_with_caches(tvmaze=tvmaze_show(), tmdb=tmdb_tv(name="TMDB Title"))
        recompute_show(show)

        # §4.7 takedown: purge the TVmaze snapshot, recompute — TMDB remains.
        show.tvmaze_cache.delete()
        show = Show.objects.get(pk=show.pk)
        recompute_show(show)
        assert show.primary_title == "TMDB Title"

        # Purge everything: content blanks, but the title never becomes empty.
        show.tmdb_cache.delete()
        show = Show.objects.get(pk=show.pk)
        recompute_show(show)
        assert show.primary_title == "TMDB Title"  # falls back to current value
        assert show.status == ""
        assert show.summary == ""
        assert show.runtime is None
        assert show.premiered is None


@pytest.mark.django_db
class TestRecomputeMovie:
    def _movie_with_cache(self, data):
        movie = Movie.objects.create(primary_title="placeholder", tmdb_id=data["id"])
        TMDBMovieCache.objects.create(movie=movie, data=data, fetched_at=timezone.now())
        return Movie.objects.get(pk=movie.pk)

    def test_passthrough_from_tmdb(self):
        movie = self._movie_with_cache(tmdb_movie())
        recompute_movie(movie)

        assert movie.primary_title == "Dune: Part Two"
        assert movie.release_date == datetime.date(2024, 2, 27)
        assert movie.runtime == 167
        assert movie.summary.startswith("Paul Atreides")

    def test_missing_title_keeps_current(self):
        movie = self._movie_with_cache(tmdb_movie(title=None))
        recompute_movie(movie)
        assert movie.primary_title == "placeholder"
