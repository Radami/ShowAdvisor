"""
JWT auth path (spec §5). The Google exchange itself is allauth/dj-rest-auth
library code needing a live Google token — not tested here; what is ours is
that issued JWTs gate the API and the refresh endpoint stays open.
"""

import datetime

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

pytestmark = pytest.mark.django_db


def _client_with(token):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


class TestJwtAuth:
    def test_valid_access_token_grants_access(self, user):
        response = _client_with(AccessToken.for_user(user)).get("/api/profile/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"username": "tester", "email": "tester@example.com"}

    def test_expired_token_rejected(self, user):
        token = AccessToken.for_user(user)
        token.set_exp(lifetime=-datetime.timedelta(minutes=1))

        response = _client_with(str(token)).get("/api/profile/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_garbage_token_rejected(self, db):
        response = _client_with("not-a-jwt").get("/api/profile/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_token_rejected(self, db):
        assert APIClient().get("/api/profile/").status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_endpoint_issues_new_access_token(self, user):
        refresh = RefreshToken.for_user(user)

        response = APIClient().post(
            "/api/auth/token/refresh/", {"refresh": str(refresh)}
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
