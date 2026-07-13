"""Catalog sync Celery tasks (spec §4.5)."""

import logging

from celery import shared_task

from .models import SyncState
from .providers import RetryPolicy, TVmazeClient, TVmazeNotFound
from .sync import upsert_show_from_tvmaze

logger = logging.getLogger(__name__)

TVMAZE_PAGE_SIZE = 250
SEED_NEXT_PAGE_KEY = "tvmaze_seed_next_page"


@shared_task
def seed_tvmaze_catalog(start_page=None, max_pages=None):
    """
    Tier 1 bulk catalog seed (§4.5): walk TVmaze's paginated show index and
    upsert a lightweight Show record (ID + core fields, no episodes) per
    entry. Resumable: the next page is checkpointed in SyncState after each
    completed page — catalog contents can't be used as the cursor, since
    Tier 3 fetches insert shows with arbitrarily high TVmaze IDs.

    `max_pages` bounds a run (useful for manual/dev runs); None walks to the
    end of the index.
    """
    if start_page is None:
        state = SyncState.objects.filter(key=SEED_NEXT_PAGE_KEY).first()
        start_page = state.value if state else 0

    client = TVmazeClient(retry_policy=RetryPolicy.BACKGROUND)
    page = start_page
    shows_synced = 0
    while max_pages is None or page - start_page < max_pages:
        try:
            payloads = client.show_index_page(page)
        except TVmazeNotFound:
            logger.info("Reached end of TVmaze show index at page %s", page)
            break
        for payload in payloads:
            upsert_show_from_tvmaze(payload)
            shows_synced += 1

        page += 1
        SyncState.objects.update_or_create(
            key=SEED_NEXT_PAGE_KEY, defaults={"value": page}
        )
        logger.info("Seeded TVmaze index page %s (%s shows so far)", page - 1, shows_synced)

    return {"start_page": start_page, "next_page": page, "shows_synced": shows_synced}
