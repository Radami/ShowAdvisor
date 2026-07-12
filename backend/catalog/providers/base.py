"""
Shared HTTP plumbing for the provider clients (spec §4.5 rate limiting):
in-process pacing between requests plus exponential backoff on 429 — no
distributed limiter, since only one worker ever runs a given sync task.
"""

import logging
import time

import requests

logger = logging.getLogger(__name__)


class ProviderClient:
    base_url = ""  # set by subclasses
    # Minimum seconds between consecutive requests from this client instance.
    request_interval = 0.0
    max_retries = 5

    def __init__(self):
        self._session = requests.Session()
        self._last_request_at = 0.0

    def _pace(self):
        if self.request_interval <= 0:
            return
        wait = self._last_request_at + self.request_interval - time.monotonic()
        if wait > 0:
            time.sleep(wait)

    def get(self, path, params=None, headers=None):
        """GET returning parsed JSON, with pacing and 429 backoff."""
        url = f"{self.base_url}{path}"
        backoff = 1.0
        for attempt in range(self.max_retries):
            self._pace()
            response = self._session.get(url, params=params, headers=headers, timeout=15)
            self._last_request_at = time.monotonic()
            if response.status_code == 429:
                logger.warning("429 from %s (attempt %s), backing off %.1fs", url, attempt + 1, backoff)
                time.sleep(backoff)
                backoff *= 2
                continue
            response.raise_for_status()
            return response.json()
        response.raise_for_status()  # surface the final 429
