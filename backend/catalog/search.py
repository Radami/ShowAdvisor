"""
Own-DB-first search (spec §4.6): pg_trgm fuzzy matching across
primary_title + alternate titles, for shows and movies. The Tier 3 provider
fallback on miss lives in the view — this module only queries locally.
"""

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q

# pg_trgm's own default similarity cutoff. icontains (also trigram-indexed)
# is OR'd in so a strict substring of a long title still matches even when
# its overall trigram similarity to the full title falls under the cutoff.
SIMILARITY_THRESHOLD = 0.3
MAX_RESULTS = 20


def _title_search(model, alternate_model, query, extra_filter, related):
    alt_ids = (
        alternate_model.objects.annotate(similarity=TrigramSimilarity("title", query))
        .filter(Q(similarity__gte=SIMILARITY_THRESHOLD) | Q(title__icontains=query))
        .values_list(f"{model._meta.model_name}_id", flat=True)
    )
    qs = (
        model.objects.annotate(similarity=TrigramSimilarity("primary_title", query))
        .filter(
            Q(similarity__gte=SIMILARITY_THRESHOLD)
            | Q(primary_title__icontains=query)
            | Q(pk__in=alt_ids)
        )
        .select_related(*related)
        .order_by("-similarity", "pk")
    )
    if extra_filter:
        qs = qs.filter(extra_filter)
    return list(qs[:MAX_RESULTS])


def search_shows(query, year=None):
    from .models import AlternateShowTitle, Show

    extra = Q(premiered__year=year) if year else None
    return _title_search(Show, AlternateShowTitle, query, extra, ("tvmaze_cache", "tmdb_cache"))


def search_movies(query, year=None):
    from .models import AlternateMovieTitle, Movie

    extra = Q(release_date__year=year) if year else None
    return _title_search(Movie, AlternateMovieTitle, query, extra, ("tmdb_cache",))
