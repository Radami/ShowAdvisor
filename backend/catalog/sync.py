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

from django.db import IntegrityError, transaction
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

# How many provider search hits a Tier 3 on-demand fetch upserts (§4.5).
ON_DEMAND_FETCH_LIMIT = 10


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

    # Never let a show-level payload (index page, search hit) clobber the
    # `_embedded` seasons/episodes of a full-detail snapshot — it also
    # serves as ensure_show_detail's "detail already fetched" marker. The
    # show-level fields still refresh from the newer payload.
    embedded = payload.get("_embedded") or {}
    existing = _cache_data(show, "tvmaze_cache")
    if "_embedded" in existing and "_embedded" not in payload:
        payload = {**payload, "_embedded": existing["_embedded"]}

    TVmazeShowCache.objects.update_or_create(
        show=show, defaults={"data": payload, "fetched_at": timezone.now()}
    )
    show.refresh_from_db()
    recompute_show(show)

    if embedded.get("episodes") or embedded.get("seasons"):
        _sync_seasons_and_episodes(show, embedded)
    return show


def _sync_seasons_and_episodes(show, embedded):
    seasons_by_number = {}
    for raw in embedded.get("seasons", []):
        # A renumbered season would leave its TVmaze ID on the old row —
        # release it first so the number-keyed upsert can't trip the unique
        # index. The old row keeps its number; rows are never deleted (§4.7).
        Season.objects.filter(tvmaze_id=raw["id"]).exclude(
            show=show, season_number=raw["number"]
        ).update(tvmaze_id=None)
        season, _ = Season.objects.update_or_create(
            show=show, season_number=raw["number"], defaults={"tvmaze_id": raw["id"]}
        )
        seasons_by_number[raw["number"]] = season

    episodes = embedded.get("episodes", [])
    _release_renumbered_episode_slots(show, episodes)
    for raw in episodes:
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


def _release_renumbered_episode_slots(show, episodes):
    """
    TVmaze renumbers episodes (and moves them across seasons). Blank the
    episode_number of every row that no longer matches the incoming numbering
    before the upsert loop, so in-place shifts and swaps can't trip
    unique_numbered_episode_per_season — the constraint exempts NULLs. The
    rows themselves survive (watched history cascades on delete, §4.4).
    """
    targets = {raw["id"]: (raw["season"], raw.get("number")) for raw in episodes}
    claimed = {
        (raw["season"], raw.get("number")) for raw in episodes if raw.get("number") is not None
    }

    stale_ids = []
    numbered = Episode.objects.filter(
        season__show=show, episode_number__isnull=False
    ).select_related("season")
    for episode in numbered:
        current = (episode.season.season_number, episode.episode_number)
        target = targets.get(episode.tvmaze_id)
        if target == current:
            continue
        # Moving in the incoming payload, or squatting on a slot the payload
        # assigns to a different episode — either way the number must go.
        if target is not None or current in claimed:
            stale_ids.append(episode.id)

    if stale_ids:
        Episode.objects.filter(id__in=stale_ids).update(episode_number=None)


def _sync_show_akas(show, akas):
    for aka in akas:
        title = aka.get("name")
        if not title or title == show.primary_title:
            continue
        country = ((aka.get("country") or {}).get("code") or "")[:2]
        AlternateShowTitle.objects.get_or_create(
            show=show, title=title[:500], country=country
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
    Tier 1 seeds and Tier 3 search hits are show-level only. "Already
    fetched" is the `_embedded` marker in the cache snapshot, not the
    presence of episodes: a legitimately episode-less show (just announced)
    must not re-trigger a synchronous provider fetch on every view.
    """
    if show.tvmaze_id and "_embedded" not in _cache_data(show, "tvmaze_cache"):
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

        # The resolved ID must be ours before anything is cached: enhancing
        # this show with a payload whose ID belongs to another Show record
        # would corrupt both (§4.2 — cross-reference IDs are ours).
        if show.tmdb_id != tmdb_id and not _claim_show_tmdb_id(show, tmdb_id):
            return show

        data = client.tv_details(tmdb_id)
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


def _claim_show_tmdb_id(show, tmdb_id):
    """
    Take ownership of a TMDB ID, relying on the unique constraint instead of
    a racy exists()-then-save check. False means another Show record already
    owns it (or won a concurrent claim) — the caller must not enhance.
    """
    original = show.tmdb_id
    show.tmdb_id = tmdb_id
    try:
        with transaction.atomic():
            show.save(update_fields=["tmdb_id"])
        return True
    except IntegrityError:
        show.tmdb_id = original
        return False


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


def fetch_shows_on_demand(query, limit=ON_DEMAND_FETCH_LIMIT):
    """
    Live TVmaze search when the local DB has no show match (§4.6). Caches
    everything fetched so future searches hit locally. Provider failures are
    logged, not raised — a search must degrade, not 500.
    """
    try:
        client = TVmazeClient()
        for hit in client.search_shows(query)[:limit]:
            show = upsert_show_from_tvmaze(hit["show"])

            # AKAs are what let the local re-query match the alias the user
            # actually typed — TVmaze finds "La Casa de Papel" as Money
            # Heist; without its AKAs our trigram search wouldn't.
            try:
                _sync_show_akas(show, client.show_akas(show.tvmaze_id))
            except TVmazeNotFound:
                pass
    except Exception:
        logger.exception("Tier 3 TVmaze fetch failed for %r", query)


def fetch_movies_on_demand(query, year=None, limit=ON_DEMAND_FETCH_LIMIT):
    """TMDB counterpart of fetch_shows_on_demand, for movies (§4.6)."""
    client = TMDBClient()
    if not client.is_configured:
        return
    try:
        results = client.search_movies(query, year=year).get("results") or []
        for payload in results[:limit]:
            upsert_movie_from_tmdb(payload)
    except Exception:
        logger.exception("Tier 3 TMDB fetch failed for %r", query)
