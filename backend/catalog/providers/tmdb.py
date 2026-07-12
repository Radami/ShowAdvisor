"""
TMDB client (spec §4.1: enhancement layer for shows, primary source for
movies). Configured via the TMDB_API_KEY environment variable — accepts
either a v3 API key or a v4 read access token (the long "eyJ..." JWT).
"""

from django.conf import settings

from .base import ProviderClient


class TMDBNotConfigured(Exception):
    """Raised when a TMDB call is attempted without an API key configured."""


class TMDBClient(ProviderClient):
    base_url = "https://api.themoviedb.org/3"
    # TMDB's JSON API limit (~40 req/s) is far above anything we do; a light
    # pace plus the base client's 429 backoff is plenty.
    request_interval = 0.05

    def __init__(self, api_key=None):
        super().__init__()
        self.api_key = api_key if api_key is not None else settings.TMDB_API_KEY

    @property
    def is_configured(self):
        return bool(self.api_key)

    def get(self, path, params=None, headers=None):
        if not self.is_configured:
            raise TMDBNotConfigured(
                "Set TMDB_API_KEY to enable TMDB (movies + show enhancement)."
            )
        params = dict(params or {})
        headers = dict(headers or {})
        if self.api_key.startswith("eyJ"):  # v4 read access token
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:  # v3 API key
            params["api_key"] = self.api_key
        return super().get(path, params=params, headers=headers)

    def search_movies(self, query, year=None):
        params = {"query": query}
        if year:
            params["year"] = year
        return self.get("/search/movie", params=params)

    def movie_details(self, tmdb_id):
        return self.get(
            f"/movie/{tmdb_id}", params={"append_to_response": "alternative_titles"}
        )

    def tv_details(self, tmdb_id):
        return self.get(
            f"/tv/{tmdb_id}", params={"append_to_response": "alternative_titles"}
        )

    def find_by_imdb_id(self, imdb_id):
        """Map an IMDb ID (from TVmaze `externals`) to TMDB records."""
        return self.get(f"/find/{imdb_id}", params={"external_source": "imdb_id"})
