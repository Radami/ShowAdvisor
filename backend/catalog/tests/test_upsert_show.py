"""
upsert_show_from_tvmaze + season/episode sync: snapshot-overwrite semantics,
the full-detail clobber guard, in-place renumbering (never delete-and-
recreate — watched history cascades on episode deletion, §4.4).
"""

import pytest

from catalog.models import Episode, Season, Show
from catalog.sync import _cache_data, _sync_show_akas, upsert_show_from_tvmaze
from tracking.models import WatchedEpisode

from .payloads import tvmaze_akas, tvmaze_episode, tvmaze_season, tvmaze_show, tvmaze_show_full

pytestmark = pytest.mark.django_db


class TestShowLevelUpsert:
    def test_creates_show_cache_and_canonical_fields(self):
        show = upsert_show_from_tvmaze(tvmaze_show())

        assert show.tvmaze_id == 250
        assert show.primary_title == "Kirby Buckets"
        assert show.status == "Ended"
        assert show.tvmaze_cache.data["id"] == 250
        assert show.tvmaze_cache.fetched_at is not None
        assert not show.seasons.exists()  # show-level payload has no episodes

    def test_reupsert_updates_in_place(self):
        upsert_show_from_tvmaze(tvmaze_show(status="Running"))
        show = upsert_show_from_tvmaze(tvmaze_show(status="Ended"))

        assert Show.objects.count() == 1
        assert show.status == "Ended"

    def test_show_level_payload_does_not_clobber_full_snapshot(self):
        upsert_show_from_tvmaze(tvmaze_show_full())
        show = upsert_show_from_tvmaze(tvmaze_show(status="Running"))

        # Show-level fields refresh, but the `_embedded` snapshot (and with
        # it the "detail already fetched" marker) must survive.
        assert show.status == "Running"
        assert "_embedded" in _cache_data(show, "tvmaze_cache")
        assert Episode.objects.filter(season__show=show).count() == 2


class TestSeasonAndEpisodeSync:
    def test_full_payload_syncs_seasons_and_episodes(self):
        show = upsert_show_from_tvmaze(tvmaze_show_full())

        season = show.seasons.get()
        assert season.season_number == 1
        assert season.tvmaze_id == 9001

        pilot = Episode.objects.get(tvmaze_id=101)
        assert pilot.episode_number == 1
        assert pilot.primary_title == "Pilot"
        assert pilot.overview == "Kirby's drawings come to life."
        assert pilot.airstamp is not None
        assert str(pilot.air_date) == "2014-10-20"

    def test_resync_updates_episodes_in_place(self):
        show = upsert_show_from_tvmaze(tvmaze_show_full())
        original_pk = Episode.objects.get(tvmaze_id=101).pk

        renamed = tvmaze_show_full(
            episodes=[tvmaze_episode(101, 1, 1, "Pilot (revised)")]
        )
        upsert_show_from_tvmaze(renamed)

        episode = Episode.objects.get(tvmaze_id=101)
        assert episode.pk == original_pk  # identity is the TVmaze ID
        assert episode.primary_title == "Pilot (revised)"
        assert show.seasons.count() == 1

    def test_watched_history_survives_resync(self, user):
        upsert_show_from_tvmaze(tvmaze_show_full())
        episode = Episode.objects.get(tvmaze_id=101)
        WatchedEpisode.objects.create(user=user, episode=episode)

        upsert_show_from_tvmaze(tvmaze_show_full())

        assert WatchedEpisode.objects.filter(user=user, episode_id=episode.pk).exists()

    def test_season_created_from_episodes_when_seasons_embed_missing(self):
        payload = tvmaze_show(
            _embedded={"episodes": [tvmaze_episode(101, 1, 1)]}
        )
        show = upsert_show_from_tvmaze(payload)

        season = show.seasons.get()
        assert season.season_number == 1
        assert season.tvmaze_id is None  # fallback creation knows no season ID

    def test_multiple_specials_allowed_per_season(self):
        payload = tvmaze_show_full(
            episodes=[
                tvmaze_episode(201, 1, None, "Special One"),
                tvmaze_episode(202, 1, None, "Special Two"),
            ]
        )
        show = upsert_show_from_tvmaze(payload)

        specials = Episode.objects.filter(season__show=show, episode_number=None)
        assert specials.count() == 2


class TestRenumbering:
    """TVmaze renumbers; unique constraints must never abort the sync."""

    def test_episode_swap(self):
        upsert_show_from_tvmaze(tvmaze_show_full())

        swapped = tvmaze_show_full(
            episodes=[
                tvmaze_episode(101, 1, 2, "Pilot"),
                tvmaze_episode(102, 1, 1, "Cheer Force One"),
            ]
        )
        upsert_show_from_tvmaze(swapped)

        assert Episode.objects.get(tvmaze_id=101).episode_number == 2
        assert Episode.objects.get(tvmaze_id=102).episode_number == 1

    def test_episode_shift_on_inserted_episode(self):
        upsert_show_from_tvmaze(tvmaze_show_full())

        # A new episode 100 takes slot 1; the existing two shift up.
        shifted = tvmaze_show_full(
            episodes=[
                tvmaze_episode(100, 1, 1, "New Cold Open"),
                tvmaze_episode(101, 1, 2, "Pilot"),
                tvmaze_episode(102, 1, 3, "Cheer Force One"),
            ]
        )
        upsert_show_from_tvmaze(shifted)

        numbers = {e.tvmaze_id: e.episode_number for e in Episode.objects.all()}
        assert numbers == {100: 1, 101: 2, 102: 3}

    def test_episode_moves_across_seasons(self):
        upsert_show_from_tvmaze(tvmaze_show_full())

        moved = tvmaze_show_full(
            seasons=[tvmaze_season(9001, 1), tvmaze_season(9002, 2)],
            episodes=[
                tvmaze_episode(101, 1, 1, "Pilot"),
                tvmaze_episode(102, 2, 1, "Cheer Force One"),
            ],
        )
        upsert_show_from_tvmaze(moved)

        episode = Episode.objects.get(tvmaze_id=102)
        assert episode.season.season_number == 2
        assert episode.episode_number == 1

    def test_episode_demoted_to_special(self):
        upsert_show_from_tvmaze(tvmaze_show_full())

        demoted = tvmaze_show_full(
            episodes=[
                tvmaze_episode(101, 1, None, "Pilot"),
                tvmaze_episode(102, 1, 1, "Cheer Force One"),
            ]
        )
        upsert_show_from_tvmaze(demoted)

        assert Episode.objects.get(tvmaze_id=101).episode_number is None
        assert Episode.objects.get(tvmaze_id=102).episode_number == 1

    def test_stale_episode_releases_claimed_slot_but_survives(self, user):
        upsert_show_from_tvmaze(tvmaze_show_full())
        stale = Episode.objects.get(tvmaze_id=101)
        WatchedEpisode.objects.create(user=user, episode=stale)

        # Episode 101 vanished from TVmaze; a new episode claims its slot.
        replaced = tvmaze_show_full(
            episodes=[
                tvmaze_episode(103, 1, 1, "Recut Pilot"),
                tvmaze_episode(102, 1, 2, "Cheer Force One"),
            ]
        )
        upsert_show_from_tvmaze(replaced)

        stale.refresh_from_db()
        assert stale.episode_number is None  # parked, not deleted
        assert WatchedEpisode.objects.filter(episode=stale).exists()
        assert Episode.objects.get(tvmaze_id=103).episode_number == 1

    def test_season_renumbered_keeps_tvmaze_id_unique(self):
        upsert_show_from_tvmaze(tvmaze_show_full())

        # Season 9001 becomes season 2 (e.g. a year-zero season inserted).
        renumbered = tvmaze_show_full(
            seasons=[tvmaze_season(9000, 1), tvmaze_season(9001, 2)],
            episodes=[
                tvmaze_episode(101, 2, 1, "Pilot"),
                tvmaze_episode(102, 2, 2, "Cheer Force One"),
            ],
        )
        show = upsert_show_from_tvmaze(renumbered)

        assert Season.objects.get(tvmaze_id=9000).season_number == 1
        assert Season.objects.get(tvmaze_id=9001).season_number == 2
        assert show.seasons.count() == 2


class TestShowAkas:
    def test_akas_created_and_idempotent(self):
        show = upsert_show_from_tvmaze(tvmaze_show())

        _sync_show_akas(show, tvmaze_akas())
        _sync_show_akas(show, tvmaze_akas())

        titles = show.alternate_titles.order_by("title")
        assert titles.count() == 2
        assert titles.filter(title="Kirby et ses potes", country="FR").exists()

    def test_primary_title_not_duplicated_as_aka(self):
        show = upsert_show_from_tvmaze(tvmaze_show())
        _sync_show_akas(show, [{"name": "Kirby Buckets", "country": None}])
        assert not show.alternate_titles.exists()

    def test_overlong_aka_truncated(self):
        show = upsert_show_from_tvmaze(tvmaze_show())
        _sync_show_akas(show, [{"name": "x" * 600, "country": None}])
        assert len(show.alternate_titles.get().title) == 500
