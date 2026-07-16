from django.urls import path

from .views import (
    EpisodeWatchedView,
    MovieSubscriptionView,
    MovieWatchedView,
    MyMoviesView,
    MyShowsView,
    SeasonWatchedView,
    ShowSubscriptionView,
    WatchHistoryView,
)

urlpatterns = [
    # Task 5.1 — mark watched / unwatched
    path("episodes/<int:pk>/watched/", EpisodeWatchedView.as_view(), name="episode_watched"),
    path("seasons/<int:pk>/watched/", SeasonWatchedView.as_view(), name="season_watched"),
    path("movies/<int:pk>/watched/", MovieWatchedView.as_view(), name="movie_watched"),
    # Task 5.2 — subscribe / unsubscribe / pause
    path("shows/<int:pk>/subscription/", ShowSubscriptionView.as_view(), name="show_subscription"),
    path("movies/<int:pk>/subscription/", MovieSubscriptionView.as_view(), name="movie_subscription"),
    # Task 5.3 — Watching / Up next / Paused + Watch History
    path("my/shows/", MyShowsView.as_view(), name="my_shows"),
    path("my/movies/", MyMoviesView.as_view(), name="my_movies"),
    path("history/", WatchHistoryView.as_view(), name="watch_history"),
]
