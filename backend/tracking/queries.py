"""
Shared release-state predicates (spec §3.1, resolved Watching/Up next rule).
`airstamp` is the source of truth for "has it aired?" (§4.4); `air_date` is
the fallback for episodes without one, and an episode with neither is
treated as unaired (announced but unscheduled).
"""

from django.db.models import Q
from django.utils import timezone


def episode_aired_q():
    now = timezone.now()
    today = timezone.localdate()
    return Q(airstamp__lte=now) | (Q(airstamp__isnull=True) & Q(air_date__lte=today))


def episode_unaired_q():
    return ~episode_aired_q()
