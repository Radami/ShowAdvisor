from django.contrib.postgres.indexes import GinIndex
from django.db import models


class Show(models.Model):
    """
    Canonical show record (spec §4.4 Catalog). Fields are merged from the
    provider caches (§4.7: TVmaze wins, TMDB fills gaps) — everything except
    the cross-reference IDs is treated as recomputable at any time.
    """

    # Canonical/merged fields. All optional: a record can exist with only
    # one provider's data, or with fields blanked after a takedown (§4.7).
    primary_title = models.CharField(max_length=500)
    status = models.CharField(max_length=50, blank=True)  # TVmaze: Running/Ended/TBD/...
    premiered = models.DateField(null=True, blank=True)
    ended = models.DateField(null=True, blank=True)
    summary = models.TextField(blank=True)
    runtime = models.PositiveIntegerField(null=True, blank=True)  # minutes
    network = models.CharField(max_length=255, blank=True)
    # TVmaze schedule shape: {"time": "21:00", "days": ["Monday"]}
    schedule = models.JSONField(null=True, blank=True)

    # Cross-reference to external providers (§4.2). Both nullable — a show
    # may be known to only one provider — but at least one must be set
    # (constraint below): a show with no provider ID is an unusable orphan.
    # Adding e.g. thetvdb_id later is a purely additive change.
    tvmaze_id = models.PositiveIntegerField(null=True, blank=True, unique=True)
    tmdb_id = models.PositiveIntegerField(null=True, blank=True, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(tvmaze_id__isnull=False) | models.Q(tmdb_id__isnull=False),
                name="show_has_provider_id",
            ),
        ]
        indexes = [
            # pg_trgm fuzzy search across primary + alternate titles (§4.6).
            GinIndex(fields=["primary_title"], name="show_title_trgm", opclasses=["gin_trgm_ops"]),
        ]

    def __str__(self):
        return self.primary_title


class AlternateShowTitle(models.Model):
    """
    Alternate/foreign-language titles for search (spec §4.6) — alternates
    only. The canonical display title lives solely on Show.primary_title;
    search matches against both.
    """

    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name="alternate_titles")
    title = models.CharField(max_length=500, db_index=True)
    country = models.CharField(max_length=2, blank=True)  # ISO 3166-1 alpha-2

    class Meta:
        constraints = [
            # Re-syncing AKAs must upsert, never duplicate.
            models.UniqueConstraint(
                fields=["show", "title", "country"],
                name="unique_alternate_show_title",
            ),
        ]
        indexes = [
            GinIndex(fields=["title"], name="alt_show_title_trgm", opclasses=["gin_trgm_ops"]),
        ]

    def __str__(self):
        return self.title


class Season(models.Model):
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name="seasons")
    season_number = models.PositiveIntegerField()
    tvmaze_id = models.PositiveIntegerField(null=True, blank=True, unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["show", "season_number"], name="unique_season_per_show"
            ),
        ]
        ordering = ["season_number"]

    def __str__(self):
        return f"{self.show} S{self.season_number}"


class Episode(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="episodes")
    # Nullable: TVmaze specials have no episode number. The unique constraint
    # below therefore only applies to numbered episodes.
    episode_number = models.PositiveIntegerField(null=True, blank=True)
    primary_title = models.CharField(max_length=500, blank=True)
    overview = models.TextField(blank=True)  # episode detail view (§3.1)
    air_date = models.DateField(null=True, blank=True)  # display
    # Exact air moment (TVmaze `airstamp`, timezone-aware) — the source of
    # truth for "has it aired?" (Watching/Up next split, §3.1) and for the
    # episode-aired notification (§5). air_date alone is ambiguous at the
    # midnight boundary.
    airstamp = models.DateTimeField(null=True, blank=True)
    runtime = models.PositiveIntegerField(null=True, blank=True)
    tvmaze_id = models.PositiveIntegerField(null=True, blank=True, unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["season", "episode_number"],
                condition=models.Q(episode_number__isnull=False),
                name="unique_numbered_episode_per_season",
            ),
        ]
        ordering = ["episode_number"]

    def __str__(self):
        number = f"E{self.episode_number}" if self.episode_number else "Special"
        return f"{self.season} {number} {self.primary_title}".strip()


class AlternateEpisodeTitle(models.Model):
    """Same alternates-only pattern as AlternateShowTitle, per episode."""

    episode = models.ForeignKey(
        Episode, on_delete=models.CASCADE, related_name="alternate_titles"
    )
    title = models.CharField(max_length=500, db_index=True)
    country = models.CharField(max_length=2, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["episode", "title", "country"],
                name="unique_alternate_episode_title",
            ),
        ]

    def __str__(self):
        return self.title


class Movie(models.Model):
    """
    Canonical movie record (spec §4.4). Single-sourced from TMDB for now
    (§4.1) — tvmaze has no movies; TheTVDB deferred (§9).
    """

    primary_title = models.CharField(max_length=500)
    release_date = models.DateField(null=True, blank=True)
    runtime = models.PositiveIntegerField(null=True, blank=True)
    summary = models.TextField(blank=True)
    # Nullable column (future providers may not have a TMDB ID) but a check
    # constraint requires at least one provider ID — currently that means
    # tmdb_id, TMDB being the only movie source (§4.1). Relaxes to an OR,
    # like Show's, when another provider is added.
    tmdb_id = models.PositiveIntegerField(null=True, blank=True, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(tmdb_id__isnull=False),
                name="movie_has_provider_id",
            ),
        ]
        indexes = [
            GinIndex(fields=["primary_title"], name="movie_title_trgm", opclasses=["gin_trgm_ops"]),
        ]

    def __str__(self):
        return self.primary_title


class AlternateMovieTitle(models.Model):
    """Alternate-title pattern of AlternateShowTitle, for movie search."""

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="alternate_titles")
    title = models.CharField(max_length=500, db_index=True)
    country = models.CharField(max_length=2, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["movie", "title", "country"],
                name="unique_alternate_movie_title",
            ),
        ]
        indexes = [
            GinIndex(fields=["title"], name="alt_movie_title_trgm", opclasses=["gin_trgm_ops"]),
        ]

    def __str__(self):
        return self.title


class SyncState(models.Model):
    """
    Durable progress markers for the sync tasks (spec §4.5) — e.g. the next
    TVmaze index page for the Tier 1 seed, later the Tier 2 delta-sync
    watermark. A dedicated table rather than something inferred from catalog
    rows: Tier 3 on-demand fetches insert shows with arbitrary provider IDs,
    so catalog contents say nothing about how far a seed walk actually got.
    Deleting a row is safe — the task restarts from the beginning.
    """

    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key} = {self.value}"


class ProviderCache(models.Model):
    """
    Base for the raw provider caches (spec §4.4, §4.7). One current snapshot
    per entity per provider — a refetch overwrites `data` and `fetched_at`
    rather than appending. Canonical records are derived from these rows;
    a takedown deletes them and triggers a recompute (§4.7).
    """

    data = models.JSONField()  # raw provider response, untransformed
    fetched_at = models.DateTimeField()

    class Meta:
        abstract = True


class TVmazeShowCache(ProviderCache):
    show = models.OneToOneField(Show, on_delete=models.CASCADE, related_name="tvmaze_cache")

    def __str__(self):
        return f"TVmaze cache for {self.show}"


class TMDBShowCache(ProviderCache):
    show = models.OneToOneField(Show, on_delete=models.CASCADE, related_name="tmdb_cache")

    def __str__(self):
        return f"TMDB cache for {self.show}"


class TMDBMovieCache(ProviderCache):
    movie = models.OneToOneField(Movie, on_delete=models.CASCADE, related_name="tmdb_cache")
    # TMDB movie payloads come in two shapes: partial search hits and full
    # /movie/{id} records. Set from the caller's declared payload kind; a
    # partial snapshot must never overwrite a row where this is True.
    is_detail = models.BooleanField(default=False)

    def __str__(self):
        return f"TMDB cache for {self.movie}"
