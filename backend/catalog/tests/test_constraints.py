"""Catalog DB integrity rules (spec §4.4) that the sync layer leans on."""

import pytest
from django.db import IntegrityError

from catalog.models import AlternateShowTitle, Episode, Movie, Season, Show

pytestmark = pytest.mark.django_db


def _show():
    return Show.objects.create(primary_title="Constrained", tvmaze_id=1)


class TestCatalogConstraints:
    def test_show_requires_a_provider_id(self):
        with pytest.raises(IntegrityError):
            Show.objects.create(primary_title="Orphan")

    def test_movie_requires_tmdb_id(self):
        with pytest.raises(IntegrityError):
            Movie.objects.create(primary_title="Orphan")

    def test_season_number_unique_per_show(self):
        show = _show()
        Season.objects.create(show=show, season_number=1)
        with pytest.raises(IntegrityError):
            Season.objects.create(show=show, season_number=1)

    def test_numbered_episode_unique_per_season(self):
        season = Season.objects.create(show=_show(), season_number=1)
        Episode.objects.create(season=season, episode_number=1)
        with pytest.raises(IntegrityError):
            Episode.objects.create(season=season, episode_number=1)

    def test_specials_exempt_from_episode_uniqueness(self):
        season = Season.objects.create(show=_show(), season_number=1)
        Episode.objects.create(season=season, episode_number=None)
        Episode.objects.create(season=season, episode_number=None)

        assert season.episodes.count() == 2

    def test_alternate_title_tuple_unique(self):
        show = _show()
        aka = {"show": show, "title": "Alt", "language": "", "country": "US"}
        AlternateShowTitle.objects.create(**aka)
        with pytest.raises(IntegrityError):
            AlternateShowTitle.objects.create(**aka)
