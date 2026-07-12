from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from tracking.models import MovieSubscription, ShowSubscription, WatchedEpisode, WatchedMovie

from .models import Movie, Season, Show
from .search import search_movies, search_shows
from .serializers import (
    MovieDetailSerializer,
    MovieSearchResultSerializer,
    ShowDetailSerializer,
    ShowSearchResultSerializer,
)
from .sync import ensure_movie_detail, ensure_show_detail, on_demand_fetch


class SearchView(APIView):
    """
    GET /api/search/?q=<title>[&year=<year>] — own-DB-first (spec §4.6),
    falling back to the Tier 3 live provider fetch (§4.5) when the local
    catalog has no match, then re-querying locally.
    """

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response({"detail": "Missing ?q= search term."}, status=400)
        year = request.query_params.get("year") or None
        if year and not year.isdigit():
            return Response({"detail": "?year= must be a number."}, status=400)

        shows = search_shows(query, year)
        movies = search_movies(query, year)
        if not shows and not movies:
            on_demand_fetch(query, year)
            shows = search_shows(query, year)
            movies = search_movies(query, year)

        # Interleave shows and movies by match quality.
        ranked = [
            (obj.similarity, ShowSearchResultSerializer(obj).data) for obj in shows
        ] + [(obj.similarity, MovieSearchResultSerializer(obj).data) for obj in movies]
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        return Response({"query": query, "results": [data for _, data in ranked]})


class ShowDetailView(APIView):
    """
    GET /api/shows/<id>/ — Show detail screen data (spec §3.1). Triggers the
    full-detail fetch for Tier 1/Tier 3 stubs (episodes not yet synced) and
    the opportunistic TMDB enhancement (§4.5) on first view.
    """

    def get(self, request, pk):
        show = get_object_or_404(Show.objects.select_related("tvmaze_cache", "tmdb_cache"), pk=pk)
        ensure_show_detail(show)
        show = (
            Show.objects.select_related("tvmaze_cache", "tmdb_cache")
            .prefetch_related(
                Prefetch("seasons", queryset=Season.objects.prefetch_related("episodes"))
            )
            .get(pk=pk)
        )
        watched_ids = set(
            WatchedEpisode.objects.filter(
                user=request.user, episode__season__show=show
            ).values_list("episode_id", flat=True)
        )
        subscription = ShowSubscription.objects.filter(user=request.user, show=show).first()
        serializer = ShowDetailSerializer(
            show,
            context={"watched_episode_ids": watched_ids, "subscription": subscription},
        )
        return Response(serializer.data)


class MovieDetailView(APIView):
    """GET /api/movies/<id>/ — Movie detail screen data (spec §3.1)."""

    def get(self, request, pk):
        movie = get_object_or_404(Movie.objects.select_related("tmdb_cache"), pk=pk)
        movie = ensure_movie_detail(movie)
        subscription = MovieSubscription.objects.filter(user=request.user, movie=movie).first()
        watched = WatchedMovie.objects.filter(user=request.user, movie=movie).exists()
        serializer = MovieDetailSerializer(
            movie, context={"subscription": subscription, "watched": watched}
        )
        return Response(serializer.data)
