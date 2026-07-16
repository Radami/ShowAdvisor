"""
Shared HTTP plumbing for the provider clients (spec §4.5 rate limiting):
in-process pacing between requests plus bounded exponential backoff on 429.
Clients are used both from Celery tasks and synchronously inside web
requests (Tier 3 search, first detail view), so how long a 429 may stall
the caller is a per-caller choice — see RetryPolicy.
"""

import logging
import time
from enum import Enum
from http import HTTPStatus

import requests

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 15
INITIAL_BACKOFF_SECONDS = 1.0


class RetryPolicy(Enum):
    """
    How patiently to retry 429s, as (attempts, cap on one backoff sleep).

    INTERACTIVE bounds the worst-case stall inside a web request (~3s of
    sleeping) so a rate-limited provider degrades the response instead of
    tripping the gunicorn timeout; BACKGROUND lets Celery tasks wait out
    longer rate-limit windows.
    """

    INTERACTIVE = (3, 2.0)
    BACKGROUND = (5, 16.0)

    @property
    def max_attempts(self):
        return self.value[0]

    @property
    def max_backoff_seconds(self):
        return self.value[1]


class ProviderClient:
    base_url = ""  # set by subclasses
    # Minimum seconds between consecutive requests from this client instance.
    request_interval = 0.0

    def __init__(self, retry_policy=RetryPolicy.INTERACTIVE):
        self.retry_policy = retry_policy
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
        backoff = INITIAL_BACKOFF_SECONDS
        for attempt in range(self.retry_policy.max_attempts):
            self._pace()
            response = self._session.get(
                url, params=params, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS
            )
            self._last_request_at = time.monotonic()
            if response.status_code != HTTPStatus.TOO_MANY_REQUESTS:
                response.raise_for_status()
                return response.json()

            # Out of attempts — no point sleeping before surfacing the 429.
            if attempt + 1 == self.retry_policy.max_attempts:
                break
            delay = min(backoff, self.retry_policy.max_backoff_seconds)
            logger.warning(
                "429 from %s (attempt %s), backing off %.1fs", url, attempt + 1, delay
            )
            time.sleep(delay)
            backoff *= 2
        response.raise_for_status()  # surface the final 429
