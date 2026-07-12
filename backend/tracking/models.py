from django.conf import settings
from django.db import models


class WatchedEpisode(models.Model):
    """
    One row per user+episode (spec §4.4) — boolean semantics, no rewatch
    tracking in Phase 1: marking watched again has no additional effect.
    watched_at is set when watched flips to True.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="watched_episodes"
    )
    episode = models.ForeignKey(
        "catalog.Episode", on_delete=models.CASCADE, related_name="watched_by"
    )
    watched = models.BooleanField(default=True)
    watched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "episode"], name="unique_user_episode"),
        ]

    def __str__(self):
        return f"{self.user} watched {self.episode}"


class WatchedMovie(models.Model):
    """Same unique-per-user+movie, no-rewatch semantics as WatchedEpisode."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="watched_movies"
    )
    movie = models.ForeignKey(
        "catalog.Movie", on_delete=models.CASCADE, related_name="watched_by"
    )
    watched = models.BooleanField(default=True)
    watched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "movie"], name="unique_user_movie"),
        ]

    def __str__(self):
        return f"{self.user} watched {self.movie}"


class ShowSubscription(models.Model):
    """Drives upcoming-episode tracking and notifications (spec §4.4)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="show_subscriptions"
    )
    show = models.ForeignKey(
        "catalog.Show", on_delete=models.CASCADE, related_name="subscribers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "show"], name="unique_show_subscription"),
        ]

    def __str__(self):
        return f"{self.user} → {self.show}"


class MovieSubscription(models.Model):
    """
    Tracks a movie before release — drives the Watching/Up next split (§3.1)
    and the movie-released notification, parallel to ShowSubscription.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="movie_subscriptions"
    )
    movie = models.ForeignKey(
        "catalog.Movie", on_delete=models.CASCADE, related_name="subscribers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "movie"], name="unique_movie_subscription"),
        ]

    def __str__(self):
        return f"{self.user} → {self.movie}"


class Rating(models.Model):
    """
    Schema designed now, feature is Phase 2 (spec §4.4) — no API/UI until
    Milestone 11. Exactly one of show/movie is set, enforced by constraint.
    The value scale is provisional until the Phase 2 design pass.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings"
    )
    show = models.ForeignKey(
        "catalog.Show", on_delete=models.CASCADE, related_name="ratings",
        null=True, blank=True,
    )
    movie = models.ForeignKey(
        "catalog.Movie", on_delete=models.CASCADE, related_name="ratings",
        null=True, blank=True,
    )
    value = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(show__isnull=False, movie__isnull=True)
                    | models.Q(show__isnull=True, movie__isnull=False)
                ),
                name="rating_exactly_one_target",
            ),
            models.UniqueConstraint(
                fields=["user", "show"],
                condition=models.Q(show__isnull=False),
                name="unique_user_show_rating",
            ),
            models.UniqueConstraint(
                fields=["user", "movie"],
                condition=models.Q(movie__isnull=False),
                name="unique_user_movie_rating",
            ),
        ]

    def __str__(self):
        return f"{self.user} rated {self.show or self.movie}: {self.value}"
