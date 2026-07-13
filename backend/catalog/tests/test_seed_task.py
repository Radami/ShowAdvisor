"""Tier 1 seed task (spec §4.5): index walk + SyncState checkpointing."""

from unittest import mock

import pytest

from catalog.models import Show, SyncState
from catalog.providers import TVmazeNotFound
from catalog.tasks import SEED_NEXT_PAGE_KEY, seed_tvmaze_catalog

from .payloads import tvmaze_show

pytestmark = pytest.mark.django_db


@pytest.fixture
def tvmaze_client(monkeypatch):
    client = mock.MagicMock()
    monkeypatch.setattr("catalog.tasks.TVmazeClient", mock.MagicMock(return_value=client))
    return client


def _index_pages(pages_by_number):
    """side_effect serving the given pages, end-of-index everywhere else."""
    def fetch(page):
        if page not in pages_by_number:
            raise TVmazeNotFound(f"/shows?page={page}")
        return pages_by_number[page]
    return fetch


class TestSeedTask:
    def test_walks_index_and_checkpoints_each_page(self, tvmaze_client):
        tvmaze_client.show_index_page.side_effect = _index_pages(
            {
                0: [tvmaze_show(1), tvmaze_show(2)],
                1: [tvmaze_show(251)],
            }
        )

        result = seed_tvmaze_catalog()

        assert Show.objects.count() == 3
        assert result == {"start_page": 0, "next_page": 2, "shows_synced": 3}
        assert SyncState.objects.get(key=SEED_NEXT_PAGE_KEY).value == 2

    def test_resumes_from_checkpoint_not_from_catalog_contents(self, tvmaze_client):
        # A Tier 3 fetch inserted a high TVmaze ID — it must not affect resume.
        Show.objects.create(primary_title="Tier 3 insert", tvmaze_id=60000)
        SyncState.objects.create(key=SEED_NEXT_PAGE_KEY, value=2)
        tvmaze_client.show_index_page.side_effect = TVmazeNotFound("end")

        result = seed_tvmaze_catalog()

        tvmaze_client.show_index_page.assert_called_once_with(2)
        assert result["start_page"] == 2

    def test_explicit_start_page_overrides_checkpoint(self, tvmaze_client):
        SyncState.objects.create(key=SEED_NEXT_PAGE_KEY, value=7)
        tvmaze_client.show_index_page.side_effect = TVmazeNotFound("end")

        seed_tvmaze_catalog(start_page=0)

        tvmaze_client.show_index_page.assert_called_once_with(0)

    def test_max_pages_bounds_the_run(self, tvmaze_client):
        tvmaze_client.show_index_page.side_effect = lambda page: [
            tvmaze_show(page * 250 + 1)
        ]

        result = seed_tvmaze_catalog(max_pages=3)

        assert tvmaze_client.show_index_page.call_count == 3
        assert result["next_page"] == 3
        assert SyncState.objects.get(key=SEED_NEXT_PAGE_KEY).value == 3
