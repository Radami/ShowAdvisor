"""Subscribe / pause / unsubscribe (task 5.2), for shows and movies."""

import pytest
from rest_framework import status

from tracking.models import MovieSubscription, ShowSubscription, SubscriptionStatus

from .factories import make_movie, make_show

pytestmark = pytest.mark.django_db


class TestShowSubscription:
    def test_subscribe_created_then_ok(self, api_client, user):
        show = make_show()

        first = api_client.post(f"/api/shows/{show.pk}/subscription/")
        second = api_client.post(f"/api/shows/{show.pk}/subscription/")

        assert first.status_code == status.HTTP_201_CREATED
        assert second.status_code == status.HTTP_200_OK
        assert ShowSubscription.objects.filter(user=user, show=show).count() == 1
        assert first.data == {"status": SubscriptionStatus.ACTIVE}

    def test_pause_and_resume(self, api_client, user):
        show = make_show()
        ShowSubscription.objects.create(user=user, show=show)

        paused = api_client.patch(
            f"/api/shows/{show.pk}/subscription/", {"status": "paused"}
        )
        assert paused.status_code == status.HTTP_200_OK
        assert paused.data == {"status": SubscriptionStatus.PAUSED}

        resumed = api_client.patch(
            f"/api/shows/{show.pk}/subscription/", {"status": "active"}
        )
        assert resumed.data == {"status": SubscriptionStatus.ACTIVE}

    def test_invalid_status_rejected(self, api_client, user):
        show = make_show()
        ShowSubscription.objects.create(user=user, show=show)

        response = api_client.patch(
            f"/api/shows/{show.pk}/subscription/", {"status": "snoozed"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_without_subscription_404s(self, api_client):
        show = make_show()
        response = api_client.patch(
            f"/api/shows/{show.pk}/subscription/", {"status": "paused"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unsubscribe_is_idempotent(self, api_client, user):
        show = make_show()
        ShowSubscription.objects.create(user=user, show=show)

        for _ in range(2):
            response = api_client.delete(f"/api/shows/{show.pk}/subscription/")
            assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not ShowSubscription.objects.filter(user=user).exists()


class TestMovieSubscription:
    def test_subscribe_pause_unsubscribe_roundtrip(self, api_client, user):
        movie = make_movie()

        assert (
            api_client.post(f"/api/movies/{movie.pk}/subscription/").status_code
            == status.HTTP_201_CREATED
        )
        assert (
            api_client.patch(
                f"/api/movies/{movie.pk}/subscription/", {"status": "paused"}
            ).data
            == {"status": SubscriptionStatus.PAUSED}
        )

        api_client.delete(f"/api/movies/{movie.pk}/subscription/")
        assert not MovieSubscription.objects.filter(user=user).exists()
