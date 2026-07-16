import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        username="tester", email="tester@example.com", password="irrelevant"
    )


@pytest.fixture
def api_client(user):
    """DRF client pre-authenticated as `user` — every endpoint requires JWT."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client
