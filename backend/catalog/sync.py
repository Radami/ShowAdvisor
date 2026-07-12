"""
Catalog sync core (spec §4.5, §4.7).

Providers write raw snapshots into the cache tables; canonical Show/Movie
fields are then *derived* from those caches by the merge functions
(`recompute_show`/`recompute_movie`) — TVmaze wins for shows, TMDB is
primary for movies and fills gaps for shows. Everything canonical is
recomputable at any time from the caches alone, which is what makes the
takedown procedure (§4.7) a purge-and-recompute.
"""

import logging
import re

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from .models import (
    AlternateMovieTitle,
    AlternateShowTitle,
    Episode,
    Movie,
    Season,
    Show,
    TMDBMovieCache,
    TMDBShowCache,
    TVmazeShowCache,
)
from .providers import TMDBClient, TMDBNotConfigured, TVmazeClient, TVmazeNotFound

logger = logging.getLogger(__name__)

TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text):
    """TVmaze summaries ship as HTML; canonical text is plain."""
    return TAG_RE.sub("", text or "").strip()


def _first(*values):
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


# --- Canonical record merge (task 3.4, spec §4.7) --------------------------


def recompute_show(show):
    """
    Derive the canonical Show fields from the provider caches: TVmaze wins,
    TMDB fills gaps. Cross-reference IDs are left untouched — they're not
    provider *content*, they're ours (§4.2).
    """
    tvmaze = _cache_data(show, "tvmaze_cache")
    tmdb = _cache_data(show, "tmdb_cache")

    tvmaze_network = (tvmaze.get("network") or {}).get("name") or (
        tvmaze.get("webChannel") or {}
    ).get("name")
    tmdb_networks = tmdb.get("networks") or []
    tmdb_runtimes = tmdb.get("episode_run_time") or []
    tmdb_ended = (
        tmdb.get("last_air_date") if tmdb.get("status") in ("Ended", "Canceled") else None
    )

    show.primary_title = _first(tvmaze.get("name"), tmdb.get("name"), show.primary_title)
    show.status = _first(tvmaze.get("status"), tmdb.get("status")) or ""
    show.premiered = _parse(parse_date, _first(tvmaze.get("premiered"), tmdb.get("first_air_date")))
    show.ended = _parse(parse_date, _first(tvmaze.get("ended"), tmdb_ended))
    show.summary = _first(strip_html(tvmaze.get("summary")), tmdb.get("overview")) or ""
    show.runtime = _first(
        tvmaze.get("runtime"),
        tvmaze.get("averageRuntime"),
        tmdb_runtimes[0] if tmdb_runtimes else None,
    )
    show.network = _first(tvmaze_network, tmdb_networks[0]["name"] if tmdb_networks else None) or ""
    show.schedule = tvmaze.get("schedule")
    show.save()
    return show


def recompute_movie(movie):
    """TMDB is the only movie source for v1 (§4.1) — merge is a passthrough."""
    tmdb = _cache_data(movie, "tmdb_cache")

    movie.primary_title = _first(tmdb.get("title"), movie.primary_title)
    movie.release_date = _parse(parse_date, tmdb.get("release_date"))
    movie.runtime = tmdb.get("runtime")
    movie.summary = tmdb.get("overview") or ""
    movie.save()
    return movie


def _cache_data(entity, attr):
    cache = getattr(entity, attr, None)
    return cache.data if cache else {}


def _parse(parser, value):
    return parser(value) if value else None


# --- TVmaze → Show ---------------------------------------------------------


@transaction.atomic
def upsert_show_from_tvmaze(payload):
    """
    Create/update a Show from a raw TVmaze show payload (index item, search
    hit, or full detail with `_embedded`). Overwrites the one-snapshot cache
    row (§4.4), recomputes the canonical record, and — when the payload has
    embedded seasons/episodes — syncs those *in place* (never delete-and-
    recreate: WatchedEpisode cascades on episode deletion).
    """
    show, _ = Show.objects.get_or_create(
        tvmaze_id=payload["id"], defaults={"primary_title": payload.get("name") or ""}
    )
    TVmazeShowCache.objects.update_or_create(
        show=show, defaults={"data": payload, "fetched_at": timezone.now()}
    )
    show.refresh_from_db()
    recompute_show(show)

    embedded = payload.get("_embedded") or {}
    if embedded.get("episodes") or embedded.get("seasons"):
        _sync_seasons_and_episodes(show, embedded)
    return show


def _sync_seasons_and_episodes(show, embedded):
    seasons_by_number = {}
    for raw in embedded.get("seasons", []):
        season, _ = Season.objects.update_or_create(
            show=show, season_number=raw["number"], defaults={"tvmaze_id": raw["id"]}
        )
        seasons_by_number[raw["number"]] = season

    for raw in embedded.get("episodes", []):
        season = seasons_by_number.get(raw["season"])
        if season is None:
            season, _ = Season.objects.get_or_create(show=show, season_number=raw["season"])
            seasons_by_number[raw["season"]] = season
        Episode.objects.update_or_create(
            tvmaze_id=raw["id"],
            defaults={
                "season": season,
                "episode_number": raw.get("number"),
                "primary_title": raw.get("name") or "",
                "overview": strip_html(raw.get("summary")),
                "air_date": _parse(parse_date, raw.get("airdate")),
                "airstamp": _parse(parse_datetime, raw.get("airstamp")),
                "runtime": raw.get("runtime"),
            },
        )


def _sync_show_akas(show, akas):
    for aka in akas:
        title = aka.get("name")
        if not title or title == show.primary_title:
            continue
        country = ((aka.get("country") or {}).get("code") or "")[:2]
        AlternateShowTitle.objects.get_or_create(
            show=show, title=title[:500], language="", country=country
        )


def fetch_show_full(show):
    """
    Full-detail fetch for one show: TVmaze detail (seasons/episodes) + AKAs,
    then opportunistic TMDB enhancement (§4.5 — TMDB is fetched the first
    time a show is shown to a user, not on a schedule).
    """
    client = TVmazeClient()
    show = upsert_show_from_tvmaze(client.show_details(show.tvmaze_id))
    try:
        _sync_show_akas(show, client.show_akas(show.tvmaze_id))
    except TVmazeNotFound:
        pass
    enhance_show_from_tmdb(show)
    return show


def ensure_show_detail(show):
    """
    Make sure a show has its full detail (episodes) before it's displayed —
    Tier 1 seeds and Tier 3 search hits are show-level only.
    """
    if show.tvmaze_id and not show.seasons.exists():
        try:
            return fetch_show_full(show)
        except Exception:
            logger.exception("Full-detail fetch failed for show %s", show.pk)
    elif not _has_cache(show, "tmdb_cache"):
        enhance_show_from_tmdb(show)
    return show


def _has_cache(entity, attr):
    return getattr(entity, attr, None) is not None


def enhance_show_from_tmdb(show):
    """
    TMDB enhancement layer for shows (§4.1): posters/extra metadata. Resolves
    the TMDB ID via the show's IMDb external ID (from the TVmaze cache) when
    we don't have one yet. Failure is never fatal — enhancement is optional.
    """
    client = TMDBClient()
    if not client.is_configured:
        return show
    try:
        tmdb_id = show.tmdb_id or _resolve_show_tmdb_id(client, show)
        if not tmdb_id:
            return show
        data = client.tv_details(tmdb_id)
        if show.tmdb_id != tmdb_id and not Show.objects.filter(tmdb_id=tmdb_id).exists():
            show.tmdb_id = tmdb_id
            show.save(update_fields=["tmdb_id"])
        TMDBShowCache.objects.update_or_create(
            show=show, defaults={"data": data, "fetched_at": timezone.now()}
        )
        show.refresh_from_db()
        recompute_show(show)
        _sync_tmdb_alternate_titles(
            show, data, AlternateShowTitle, "show"
        )
    except TMDBNotConfigured:
        pass
    except Exception:
        logger.exception("TMDB enhancement failed for show %s", show.pk)
    return show


def _resolve_show_tmdb_id(client, show):
    imdb_id = (_cache_data(show, "tvmaze_cache").get("externals") or {}).get("imdb")
    if not imdb_id:
        return None
    results = client.find_by_imdb_id(imdb_id).get("tv_results") or []
    return results[0]["id"] if results else None


def _sync_tmdb_alternate_titles(entity, data, title_model, fk_name):
    titles = (data.get("alternative_titles") or {})
    # Movies nest under "titles", TV under "results".
    for alt in titles.get("titles") or titles.get("results") or []:
        title = alt.get("title")
        if not title or title == entity.primary_title:
            continue
        title_model.objects.get_or_create(
            **{fk_name: entity},
            title=title[:500],
            language="",
            country=(alt.get("iso_3166_1") or "")[:2],
        )


# --- TMDB → Movie ----------------------------------------------------------


@transaction.atomic
def upsert_movie_from_tmdb(payload):
    """
    Create/update a Movie from a raw TMDB movie payload (search hit or full
    detail). Same snapshot-overwrite + recompute pattern as shows.
    """
    movie, _ = Movie.objects.get_or_create(
        tmdb_id=payload["id"], defaults={"primary_title": payload.get("title") or ""}
    )
    existing = _cache_data(movie, "tmdb_cache")
    # Never let a partial search-hit payload clobber a full-detail snapshot.
    if "runtime" in existing and "runtime" not in payload:
        return movie
    TMDBMovieCache.objects.update_or_create(
        movie=movie, defaults={"data": payload, "fetched_at": timezone.now()}
    )
    movie.refresh_from_db()
    recompute_movie(movie)
    _sync_tmdb_alternate_titles(movie, payload, AlternateMovieTitle, "movie")
    return movie


def ensure_movie_detail(movie):
    """
    Search hits from TMDB are partial (no runtime/alternate titles) — fetch
    the full record before the movie is displayed.
    """
    if "runtime" in _cache_data(movie, "tmdb_cache"):
        return movie
    client = TMDBClient()
    if not client.is_configured or not movie.tmdb_id:
        return movie
    try:
        return upsert_movie_from_tmdb(client.movie_details(movie.tmdb_id))
    except Exception:
        logger.exception("Full-detail fetch failed for movie %s", movie.pk)
        return movie


# --- Tier 3: on-demand fetch on search miss (task 3.3, §4.5) ---------------


def on_demand_fetch(query, year=None, limit=10):
    """
    Live provider search when the local DB has no match (§4.6). Caches
    everything fetched so future searches hit locally. Provider failures are
    logged, not raised — a search must degrade, not 500.
    """
    try:
        for hit in TVmazeClient().search_shows(query)[:limit]:
            upsert_show_from_tvmaze(hit["show"])
    except Exception:
        logger.exception("Tier 3 TVmaze fetch failed for %r", query)

    tmdb = TMDBClient()
    if tmdb.is_configured:
        try:
            results = tmdb.search_movies(query, year=year).get("results") or []
            for payload in results[:limit]:
                upsert_movie_from_tmdb(payload)
        except Exception:
            logger.exception("Tier 3 TMDB fetch failed for %r", query)
