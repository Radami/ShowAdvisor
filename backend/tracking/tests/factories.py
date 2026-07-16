"""
Minimal ORM factories for tracking tests. Air/release timing is expressed
as a day offset from now (negative = in the past), which is what every
bucket test actually varies; None means unscheduled/unknown.
"""

import datetime
import itertools

from django.utils import timezone

from catalog.models import Episode, Movie, Season, Show

_ids = itertools.count(1)


def make_show(title="Test Show", **fields):
    return Show.objects.create(primary_title=title, tvmaze_id=next(_ids), **fields)


def make_season(show, number=1):
    return Season.objects.create(show=show, season_number=number)


def make_episode(season, number, airs_in_days=-7, **fields):
    """Negative offset = aired, positive = upcoming, None = unscheduled."""
    if airs_in_days is None:
        airstamp = None
        air_date = None
    else:
        airstamp = timezone.now() + datetime.timedelta(days=airs_in_days)
        air_date = airstamp.date()
    return Episode.objects.create(
        season=season,
        episode_number=number,
        primary_title=f"Episode {number}",
        airstamp=airstamp,
        air_date=air_date,
        **fields,
    )


def make_movie(title="Test Movie", releases_in_days=-30, **fields):
    """Same offset convention as make_episode; None = no release date."""
    release_date = (
        None
        if releases_in_days is None
        else timezone.localdate() + datetime.timedelta(days=releases_in_days)
    )
    return Movie.objects.create(
        primary_title=title, tmdb_id=next(_ids), release_date=release_date, **fields
    )
