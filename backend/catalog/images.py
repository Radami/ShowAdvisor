"""
Poster URL resolution (spec §4.5): images are hotlinked from the providers'
CDNs — only paths/URLs live in the raw caches, no binaries are stored. The
API returns a ready-to-load URL so the mobile app doesn't need per-provider
URL-building rules.
"""

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"


def _cache_data(entity, attr):
    cache = getattr(entity, attr, None)
    return cache.data if cache else {}


def show_poster_url(show):
    """TMDB poster preferred (§4.1 enhancement layer), TVmaze image fallback."""
    path = _cache_data(show, "tmdb_cache").get("poster_path")
    if path:
        return f"{TMDB_IMAGE_BASE}{path}"
    image = _cache_data(show, "tvmaze_cache").get("image") or {}
    return image.get("medium") or image.get("original")


def movie_poster_url(movie):
    path = _cache_data(movie, "tmdb_cache").get("poster_path")
    return f"{TMDB_IMAGE_BASE}{path}" if path else None
