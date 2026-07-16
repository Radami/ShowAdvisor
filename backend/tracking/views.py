from django.db.models import Count, Min
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.images import movie_poster_url, show_poster_url
from catalog.models import Episode, Movie, Season, Show

from .models import (
    MovieSubscription,
    ShowSubscription,
    SubscriptionStatus,
    WatchedEpisode,
    WatchedMovie,
)
from .queries import episode_aired_q, episode_unaired_q

HISTORY_DEFAULT_LIMIT = 100
HISTORY_MAX_LIMIT = 500


# --- Task 5.1: mark watched / unwatched (presence semantics, spec §4.4) ----


class EpisodeWatchedView(APIView):
    """POST marks watched (idempotent — no rewatch tracking), DELETE unwatches."""

    def post(self, request, pk):
        episode = get_object_or_404(Episode, pk=pk)
        WatchedEpisode.objects.get_or_create(user=request.user, episode=episode)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, pk):
        WatchedEpisode.objects.filter(user=request.user, episode_id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SeasonWatchedView(APIView):
    """The "mark season watched" bulk shortcut (spec §3.1)."""

    def post(self, request, pk):
        season = get_object_or_404(Season, pk=pk)
        # Aired episodes only — you can't have watched the future, and
        # marking it would silently drain Up next as episodes air.
        WatchedEpisode.objects.bulk_create(
            [
                WatchedEpisode(user=request.user, episode=episode)
                for episode in season.episodes.filter(episode_aired_q())
            ],
            ignore_conflicts=True,  # already-watched episodes stay as they are
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, pk):
        WatchedEpisode.objects.filter(user=request.user, episode__season_id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MovieWatchedView(APIView):
    def post(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        WatchedMovie.objects.get_or_create(user=request.user, movie=movie)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, pk):
        WatchedMovie.objects.filter(user=request.user, movie_id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Task 5.2: subscribe / unsubscribe / pause (spec §4.4) -----------------


class BaseSubscriptionView(APIView):
    """
    POST subscribes (idempotent), PATCH {"status": "active"|"paused"}
    pauses/resumes ("watch later"), DELETE unsubscribes.
    """

    subscription_model = None
    target_model = None
    target_field = ""  # "show" or "movie"

    def post(self, request, pk):
        target = get_object_or_404(self.target_model, pk=pk)
        subscription, created = self.subscription_model.objects.get_or_create(
            user=request.user, **{self.target_field: target}
        )
        return Response(
            {"status": subscription.status},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        new_status = request.data.get("status")
        if new_status not in SubscriptionStatus.values:
            return Response(
                {"detail": f"status must be one of {SubscriptionStatus.values}."},
                status=400,
            )
        subscription = get_object_or_404(
            self.subscription_model, user=request.user, **{f"{self.target_field}_id": pk}
        )
        subscription.status = new_status
        subscription.save(update_fields=["status"])
        return Response({"status": subscription.status})

    def delete(self, request, pk):
        self.subscription_model.objects.filter(
            user=request.user, **{f"{self.target_field}_id": pk}
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShowSubscriptionView(BaseSubscriptionView):
    subscription_model = ShowSubscription
    target_model = Show
    target_field = "show"


class MovieSubscriptionView(BaseSubscriptionView):
    subscription_model = MovieSubscription
    target_model = Movie
    target_field = "movie"


# --- Task 5.3: Watch list / Up next / Paused + Watch History (spec §3.1) ---


class MyShowsView(APIView):
    """
    GET /api/my/shows/ — the three buckets (spec §3.1, resolved): Watch list =
    every active subscription until *all* of the show's episodes are watched
    (partially watched and fully-caught-up-but-still-running shows stay);
    Up next = active subscription with unaired episodes (a show is usually in
    both); Paused = everything paused, regardless of state.
    """

    def get(self, request):
        subscriptions = ShowSubscription.objects.filter(user=request.user).select_related(
            "show", "show__tvmaze_cache", "show__tmdb_cache"
        )
        active_ids = [s.show_id for s in subscriptions if s.status == SubscriptionStatus.ACTIVE]

        episode_totals = dict(
            Episode.objects.filter(season__show_id__in=active_ids)
            .values_list("season__show_id")
            .annotate(count=Count("id"))
        )
        unwatched_totals = dict(
            Episode.objects.filter(season__show_id__in=active_ids)
            .exclude(watched_by__user=request.user)
            .values_list("season__show_id")
            .annotate(count=Count("id"))
        )
        aired_unwatched = dict(
            Episode.objects.filter(episode_aired_q(), season__show_id__in=active_ids)
            .exclude(watched_by__user=request.user)
            .values_list("season__show_id")
            .annotate(count=Count("id"))
        )
        next_airstamps = dict(
            Episode.objects.filter(episode_unaired_q(), season__show_id__in=active_ids)
            .values_list("season__show_id")
            .annotate(next=Min("airstamp"))
        )

        watch_list, up_next, paused = [], [], []
        for subscription in subscriptions:
            show = subscription.show
            item = self._item(show, subscription)
            if subscription.status == SubscriptionStatus.PAUSED:
                paused.append(item)
                continue
            item["unwatched_count"] = aired_unwatched.get(show.id, 0)
            item["next_airstamp"] = next_airstamps.get(show.id)
            # "Fully watched" requires the show to have episodes at all — a
            # just-subscribed show whose episodes haven't been synced yet
            # stays on the watch list rather than silently vanishing.
            if unwatched_totals.get(show.id) or show.id not in episode_totals:
                watch_list.append(item)
            if show.id in next_airstamps:
                up_next.append(item)
        return Response({"watch_list": watch_list, "up_next": up_next, "paused": paused})

    def _item(self, show, subscription):
        return {
            "id": show.id,
            "title": show.primary_title,
            "status": show.status,
            "poster_url": show_poster_url(show),
            "subscription_status": subscription.status,
        }


class MyMoviesView(APIView):
    """
    GET /api/my/movies/ — same three buckets for movies: Watch list = every
    active subscription until the movie is watched (released or not); Up
    next = unreleased (no release date counts as unreleased — an unreleased
    movie is in both); Paused = paused. Watched movies drop out (visible in
    Watch History only, spec §3.1).
    """

    def get(self, request):
        subscriptions = MovieSubscription.objects.filter(user=request.user).select_related(
            "movie", "movie__tmdb_cache"
        )
        watched_ids = set(
            WatchedMovie.objects.filter(
                user=request.user, movie_id__in=[s.movie_id for s in subscriptions]
            ).values_list("movie_id", flat=True)
        )
        today = timezone.localdate()

        watch_list, up_next, paused = [], [], []
        for subscription in subscriptions:
            movie = subscription.movie
            item = {
                "id": movie.id,
                "title": movie.primary_title,
                "release_date": movie.release_date,
                "poster_url": movie_poster_url(movie),
                "subscription_status": subscription.status,
            }
            if subscription.status == SubscriptionStatus.PAUSED:
                paused.append(item)
                continue

            # Watched movies drop out of both buckets — Watch History is
            # the only place they remain visible (§3.1).
            if movie.id in watched_ids:
                continue
            watch_list.append(item)
            if not movie.release_date or movie.release_date > today:
                up_next.append(item)
        return Response({"watch_list": watch_list, "up_next": up_next, "paused": paused})


class WatchHistoryView(APIView):
    """
    GET /api/history/[?limit=N] — everything the user has marked watched,
    most recent first (spec §3.1 Watch History screen).
    """

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", HISTORY_DEFAULT_LIMIT))
        except ValueError:
            return Response(
                {"detail": "?limit= must be a number."}, status=status.HTTP_400_BAD_REQUEST
            )
        # Clamp rather than error: a negative value would make the queryset
        # slice below raise, turning bad input into a 500.
        limit = min(max(limit, 0), HISTORY_MAX_LIMIT)

        episodes = (
            WatchedEpisode.objects.filter(user=request.user)
            .select_related("episode", "episode__season", "episode__season__show")
            .order_by("-watched_at")[:limit]
        )
        movies = (
            WatchedMovie.objects.filter(user=request.user)
            .select_related("movie")
            .order_by("-watched_at")[:limit]
        )

        items = [
            {
                "type": "episode",
                "watched_at": watched.watched_at,
                "show_id": watched.episode.season.show_id,
                "show_title": watched.episode.season.show.primary_title,
                "season_number": watched.episode.season.season_number,
                "episode_number": watched.episode.episode_number,
                "episode_id": watched.episode_id,
                "title": watched.episode.primary_title,
            }
            for watched in episodes
        ] + [
            {
                "type": "movie",
                "watched_at": watched.watched_at,
                "movie_id": watched.movie_id,
                "title": watched.movie.primary_title,
            }
            for watched in movies
        ]
        items.sort(key=lambda item: item["watched_at"], reverse=True)
        return Response({"history": items[:limit]})
