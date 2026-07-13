"""Tracking DB integrity rules: presence-semantics rows must be unique."""

import pytest
from django.db import IntegrityError

from tracking.models import Rating, ShowSubscription, WatchedEpisode

from .factories import make_episode, make_movie, make_season, make_show

pytestmark = pytest.mark.django_db


class TestTrackingConstraints:
    def test_watched_episode_unique_per_user(self, user):
        episode = make_episode(make_season(make_show()), 1)
        WatchedEpisode.objects.create(user=user, episode=episode)
        with pytest.raises(IntegrityError):
            WatchedEpisode.objects.create(user=user, episode=episode)

    def test_show_subscription_unique_per_user(self, user):
        show = make_show()
        ShowSubscription.objects.create(user=user, show=show)
        with pytest.raises(IntegrityError):
            ShowSubscription.objects.create(user=user, show=show)

    def test_rating_rejects_two_targets(self, user):
        with pytest.raises(IntegrityError):
            Rating.objects.create(user=user, show=make_show(), movie=make_movie(), value=8)

    def test_rating_rejects_no_target(self, user):
        with pytest.raises(IntegrityError):
            Rating.objects.create(user=user, value=8)

    def test_one_rating_per_user_per_show(self, user):
        show = make_show()
        Rating.objects.create(user=user, show=show, value=8)
        with pytest.raises(IntegrityError):
            Rating.objects.create(user=user, show=show, value=9)
