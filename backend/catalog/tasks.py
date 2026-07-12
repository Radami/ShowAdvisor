"""Catalog sync Celery tasks (spec §4.5)."""

import logging

from celery import shared_task
from django.db.models import Max

from .models import Show
from .providers import TVmazeClient, TVmazeNotFound
from .sync import upsert_show_from_tvmaze

logger = logging.getLogger(__name__)

TVMAZE_PAGE_SIZE = 250


@shared_task
def seed_tvmaze_catalog(start_page=None, max_pages=None):
    """
    Tier 1 bulk catalog seed (§4.5): walk TVmaze's paginated show index and
    upsert a lightweight Show record (ID + core fields, no episodes) per
    entry. Resumable: TVmaze pages are ID-based (page = id // 250), so the
    highest tvmaze_id already stored tells us where to pick up — re-running
    the last partial page just re-upserts.

    `max_pages` bounds a run (useful for manual/dev runs); None walks to the
    end of the index.
    """
    if start_page is None:
        max_id = Show.objects.aggregate(max_id=Max("tvmaze_id"))["max_id"] or 0
        start_page = max_id // TVMAZE_PAGE_SIZE

    client = TVmazeClient()
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
        logger.info("Seeded TVmaze index page %s (%s shows so far)", page, shows_synced)
        page += 1

    return {"start_page": start_page, "next_page": page, "shows_synced": shows_synced}
