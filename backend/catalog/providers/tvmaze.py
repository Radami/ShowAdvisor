"""
TVmaze client (spec §4.1: primary/core data source; §4.5 pacing: ~0.5s
between calls keeps us under TVmaze's 20 calls / 10s limit).
"""

import requests

from .base import ProviderClient


class TVmazeNotFound(Exception):
    pass


class TVmazeClient(ProviderClient):
    base_url = "https://api.tvmaze.com"
    request_interval = 0.5

    def get(self, path, params=None, headers=None):
        try:
            return super().get(path, params=params, headers=headers)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                raise TVmazeNotFound(path) from exc
            raise

    def show_index_page(self, page):
        """
        Tier 1 bulk seed (§4.5): 250 shows per page, ID-based pagination
        (page N holds IDs N*250..N*250+249). Raises TVmazeNotFound past the
        last page.
        """
        return self.get("/shows", params={"page": page})

    def show_details(self, tvmaze_id):
        """Full show record with seasons and episodes embedded."""
        return self.get(
            f"/shows/{tvmaze_id}",
            params={"embed[]": ["seasons", "episodes"]},
        )

    def show_akas(self, tvmaze_id):
        """Alternate/foreign-language titles (§4.6)."""
        return self.get(f"/shows/{tvmaze_id}/akas")

    def search_shows(self, query):
        """Fuzzy show search — Tier 3 on-demand fetch (§4.5)."""
        return self.get("/search/shows", params={"q": query})

    def show_updates(self, since=None):
        """Map of show ID → last-updated epoch, for Tier 2 delta sync (§4.5)."""
        params = {"since": since} if since else None
        return self.get("/updates/shows", params=params)
