"""
Provider HTTP plumbing (spec §4.5): pacing, bounded 429 backoff per
RetryPolicy, and per-provider wiring (TVmaze 404s, TMDB auth flavors).
Real HTTP is stubbed with `responses`; sleeps are recorded, never slept.
"""

import pytest
import requests
import responses

from catalog.providers import RetryPolicy, TMDBClient, TMDBNotConfigured, TVmazeClient, TVmazeNotFound
from catalog.providers.base import ProviderClient

FAKE_BASE = "https://provider.test"


class FakeClient(ProviderClient):
    base_url = FAKE_BASE


class PacedClient(ProviderClient):
    base_url = FAKE_BASE
    request_interval = 0.5


@pytest.fixture
def sleeps(monkeypatch):
    calls = []
    monkeypatch.setattr("catalog.providers.base.time.sleep", calls.append)
    return calls


class TestBackoff:
    @responses.activate
    def test_success_returns_parsed_json(self, sleeps):
        responses.get(f"{FAKE_BASE}/thing", json={"ok": True})
        assert FakeClient().get("/thing") == {"ok": True}
        assert sleeps == []

    @responses.activate
    def test_429_retried_then_succeeds(self, sleeps):
        responses.get(f"{FAKE_BASE}/thing", status=429)
        responses.get(f"{FAKE_BASE}/thing", json={"ok": True})

        assert FakeClient().get("/thing") == {"ok": True}
        assert len(responses.calls) == 2
        assert sleeps == [1.0]

    @responses.activate
    def test_interactive_policy_gives_up_quickly(self, sleeps):
        for _ in range(RetryPolicy.INTERACTIVE.max_attempts):
            responses.get(f"{FAKE_BASE}/thing", status=429)

        with pytest.raises(requests.HTTPError):
            FakeClient().get("/thing")

        assert len(responses.calls) == RetryPolicy.INTERACTIVE.max_attempts
        # Backoff between attempts only — no pointless sleep after the last.
        assert sleeps == [1.0, 2.0]

    @responses.activate
    def test_background_policy_waits_out_longer_windows(self, sleeps):
        for _ in range(RetryPolicy.BACKGROUND.max_attempts):
            responses.get(f"{FAKE_BASE}/thing", status=429)

        with pytest.raises(requests.HTTPError):
            FakeClient(retry_policy=RetryPolicy.BACKGROUND).get("/thing")

        assert len(responses.calls) == RetryPolicy.BACKGROUND.max_attempts
        assert sleeps == [1.0, 2.0, 4.0, 8.0]

    @responses.activate
    def test_non_429_errors_are_not_retried(self, sleeps):
        responses.get(f"{FAKE_BASE}/thing", status=500)

        with pytest.raises(requests.HTTPError):
            FakeClient().get("/thing")

        assert len(responses.calls) == 1
        assert sleeps == []

    @responses.activate
    def test_consecutive_requests_are_paced(self, sleeps):
        responses.get(f"{FAKE_BASE}/thing", json={})
        responses.get(f"{FAKE_BASE}/thing", json={})

        client = PacedClient()
        client.get("/thing")  # first call never waits
        client.get("/thing")

        assert len(sleeps) == 1
        assert 0.0 < sleeps[0] <= PacedClient.request_interval


class TestTVmazeClient:
    @responses.activate
    def test_404_becomes_not_found(self, sleeps):
        responses.get("https://api.tvmaze.com/shows/999999", status=404)
        with pytest.raises(TVmazeNotFound):
            TVmazeClient().show_details(999999)

    @responses.activate
    def test_show_details_embeds_seasons_and_episodes(self, sleeps):
        responses.get("https://api.tvmaze.com/shows/250", json={"id": 250})
        TVmazeClient().show_details(250)

        url = responses.calls[0].request.url
        assert "embed%5B%5D=seasons" in url
        assert "embed%5B%5D=episodes" in url


class TestTMDBClient:
    def test_unconfigured_client_refuses_requests(self):
        client = TMDBClient(api_key="")
        assert not client.is_configured
        with pytest.raises(TMDBNotConfigured):
            client.get("/anything")

    @responses.activate
    def test_v3_key_sent_as_query_param(self, sleeps):
        responses.get("https://api.themoviedb.org/3/movie/1", json={})
        TMDBClient(api_key="v3-secret").movie_details(1)

        request = responses.calls[0].request
        assert "api_key=v3-secret" in request.url
        assert "Authorization" not in request.headers

    @responses.activate
    def test_v4_token_sent_as_bearer_header(self, sleeps):
        responses.get("https://api.themoviedb.org/3/movie/1", json={})
        TMDBClient(api_key="eyJhbGciOiJIUzI1NiJ9.token").movie_details(1)

        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer eyJhbGciOiJIUzI1NiJ9.token"
        assert "api_key" not in request.url
