from __future__ import annotations

import itertools

from datetime import datetime, timedelta

import numpy

from django.db.models import Count, DateTimeField, ExpressionWrapper, F, Q, QuerySet
from django.utils import timezone

from radiofeed.podcasts.models import Podcast

MAX_INTERVAL = timedelta(days=14)
MIN_INTERVAL = timedelta(hours=1)


def schedule_podcasts_for_update() -> QuerySet[Podcast]:
    """Returns podcasts scheduled for feed update:

    1. Any podcasts with pub_date or parsed NULL (i.e. recently added)
    2. Any subscribed or promoted podcasts last updated > 1 hour ago
    3. Any podcasts where distance between last pub date + refresh interval > current time and
        distance < 14 days
    4. Any podcasts last updated > 14 days ago
    """

    now = timezone.now()

    return (
        Podcast.objects.annotate(
            subscribers=Count("subscription"),
            scheduled=ExpressionWrapper(
                F("pub_date") + F("refresh_interval"),
                output_field=DateTimeField(),
            ),
        )
        .filter(
            Q(parsed__isnull=True)
            | Q(
                Q(subscribers__gt=0)
                | Q(promoted=True)
                | Q(pub_date__isnull=True)
                | Q(pub_date__gte=now - MAX_INTERVAL, scheduled__lt=now),
                parsed__lt=now - MIN_INTERVAL,
            )
            | Q(parsed__lt=now - MAX_INTERVAL),
            active=True,
        )
        .order_by(
            F("subscribers").desc(),
            F("promoted").desc(),
            F("parsed").asc(nulls_first=True),
            F("pub_date").desc(nulls_first=True),
            F("created").desc(),
        )
    )


def calculate_refresh_interval(
    pub_dates: list[datetime], since: timedelta = timedelta(days=90)
) -> timedelta:
    """Calculates the mean time interval between pub dates of individual
    episodes in a podcast.

    If latest pub date > 2 weeks returns max interval of 14 days.
    """

    now = timezone.now()

    try:

        if max(pub_dates) < now - MAX_INTERVAL:
            return MAX_INTERVAL

        relevant = now - since

        intervals = filter(
            None,
            [
                (a - b).total_seconds()
                for a, b in itertools.pairwise(
                    filter(
                        lambda pub_date: pub_date > relevant,
                        sorted(pub_dates + [now], reverse=True),
                    )
                )
            ],
        )

        return min(
            max(
                timedelta(seconds=numpy.mean(list(intervals))),
                MIN_INTERVAL,
            ),
            MAX_INTERVAL,
        )

    except ValueError:
        return MIN_INTERVAL
