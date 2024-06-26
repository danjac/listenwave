from datetime import timedelta

import pytest
from django.utils import timezone

from radiofeed.feedparser import scheduler
from radiofeed.feedparser.models import Feed, Item
from radiofeed.feedparser.tests.factories import FeedFactory, ItemFactory
from radiofeed.podcasts.models import Podcast
from radiofeed.podcasts.tests.factories import PodcastFactory


def assert_hours_diff(delta, hours):
    assert delta.total_seconds() / 3600 == pytest.approx(hours)


class TestNextScheduledUpdate:
    def test_pub_date_none(self):
        now = timezone.now()
        podcast = Podcast(
            parsed=now - timedelta(hours=1), pub_date=None, frequency=timedelta(hours=3)
        )
        assert_hours_diff(scheduler.next_scheduled_update(podcast) - now, 2)

    def test_frequency_none(self):
        now = timezone.now()
        podcast = Podcast(
            parsed=now - timedelta(hours=1), pub_date=None, frequency=None
        )
        assert (scheduler.next_scheduled_update(podcast) - now).total_seconds() < 10

    def test_parsed_none(self):
        now = timezone.now()
        podcast = Podcast(
            pub_date=now - timedelta(hours=3), parsed=None, frequency=timedelta(hours=3)
        )
        assert (scheduler.next_scheduled_update(podcast) - now).total_seconds() < 10

    def test_parsed_gt_max(self):
        now = timezone.now()
        podcast = Podcast(
            pub_date=now,
            parsed=now,
            frequency=timedelta(days=30),
        )
        assert_hours_diff(scheduler.next_scheduled_update(podcast) - now, 72)

    def test_parsed_lt_now(self):
        now = timezone.now()
        podcast = Podcast(
            pub_date=now - timedelta(days=5),
            parsed=now - timedelta(days=16),
            frequency=timedelta(days=30),
        )
        assert (scheduler.next_scheduled_update(podcast) - now).total_seconds() < 10

    def test_pub_date_lt_now(self):
        now = timezone.now()
        podcast = Podcast(
            pub_date=now - timedelta(days=33),
            parsed=now - timedelta(days=3),
            frequency=timedelta(days=30),
        )
        assert (scheduler.next_scheduled_update(podcast) - now).total_seconds() < 10

    def test_pub_date_in_future(self):
        now = timezone.now()
        podcast = Podcast(
            pub_date=now - timedelta(days=1),
            parsed=now - timedelta(hours=1),
            frequency=timedelta(days=7),
        )
        assert_hours_diff(scheduler.next_scheduled_update(podcast) - now, 71)

    def test_pub_date_lt_min(self):
        now = timezone.now()
        podcast = Podcast(
            pub_date=now - timedelta(hours=3),
            parsed=now - timedelta(minutes=30),
            frequency=timedelta(hours=3),
        )

        assert_hours_diff(scheduler.next_scheduled_update(podcast) - now, 0.5)


class TestGetScheduledForUpdate:
    @pytest.mark.parametrize(
        ("kwargs", "exists"),
        [
            pytest.param(
                {},
                True,
                id="parsed and frequency are None",
            ),
            pytest.param(
                {"frequency": timedelta(hours=3)},
                True,
                id="parsed is None",
            ),
            pytest.param(
                {"parsed": timedelta(hours=3)},
                True,
                id="frequency is None",
            ),
            pytest.param(
                {
                    "parsed": timedelta(hours=3),
                    "frequency": timedelta(hours=1),
                },
                True,
                id="pub date is None",
            ),
            pytest.param(
                {
                    "parsed": timedelta(seconds=1200),
                    "pub_date": timedelta(days=3),
                    "frequency": timedelta(hours=3),
                },
                False,
                id="just parsed",
            ),
            pytest.param(
                {
                    "parsed": timedelta(hours=3),
                    "pub_date": timedelta(days=3),
                    "frequency": timedelta(hours=3),
                },
                True,
                id="parsed before pub date+frequency",
            ),
            pytest.param(
                {
                    "parsed": timedelta(days=8),
                    "pub_date": timedelta(days=8),
                    "frequency": timedelta(days=15),
                },
                True,
                id="parsed just before max frequency",
            ),
            pytest.param(
                {
                    "parsed": timedelta(days=30),
                    "pub_date": timedelta(days=90),
                    "frequency": timedelta(days=30),
                },
                True,
                id="parsed before max frequency",
            ),
        ],
    )
    @pytest.mark.django_db()
    def test_get_scheduled_podcasts(self, kwargs, exists):
        now = timezone.now()

        frequency = kwargs.get("frequency", None)
        parsed = kwargs.get("parsed", None)
        pub_date = kwargs.get("pub_date", None)

        PodcastFactory(
            frequency=frequency,
            parsed=now - parsed if parsed else None,
            pub_date=now - pub_date if pub_date else None,
        )

        assert scheduler.get_scheduled_podcasts().exists() is exists


class TestReschedule:
    def test_pub_date_none(self):
        assert_hours_diff(scheduler.reschedule(None, timedelta(hours=24)), 24)

    def test_frequency_none(self):
        assert_hours_diff(scheduler.reschedule(timezone.now(), None), 24)

    def test_reschedule_no_change(self):
        assert scheduler.reschedule(timezone.now(), timedelta(days=10)).days == 10

    def test_increment(self):
        assert_hours_diff(
            scheduler.reschedule(
                timezone.now() - timedelta(days=1), timedelta(hours=24)
            ),
            24.24,
        )


class TestSchedule:
    def test_single_date(self):
        feed = Feed(
            **FeedFactory(
                items=[
                    Item(
                        **ItemFactory(
                            pub_date=timezone.now() - timedelta(days=3),
                        )
                    )
                ],
            )
        )

        assert scheduler.schedule(feed).days == 3

    def test_single_date_rescheduled(self):
        feed = Feed(
            **FeedFactory(
                items=[
                    Item(
                        **ItemFactory(
                            pub_date=timezone.now() - timedelta(days=33),
                        )
                    )
                ],
            )
        )

        assert scheduler.schedule(feed).days == 33

    def test_median_empty(self):
        pub_date = timezone.now() - timedelta(days=3)

        items = [Item(**ItemFactory(pub_date=pub_date)) for _ in range(12)]

        feed = Feed(**FeedFactory(items=items))

        assert scheduler.schedule(feed).days == 3

    def test_no_outliers(self):
        items = []
        last = timezone.now()

        for day in [7] * 12:
            pub_date = last - timedelta(days=day)
            items.append(Item(**ItemFactory(pub_date=pub_date)))
            last = pub_date

        feed = Feed(**FeedFactory(items=items))

        assert scheduler.schedule(feed).days == pytest.approx(7)

    def test_variation(self):
        items = []
        last = timezone.now()

        for day in [4, 3, 4, 2, 5, 2, 4, 4, 3, 4, 4, 4, 6, 5, 7, 7, 7, 7, 3]:
            pub_date = last - timedelta(days=day)
            items.append(Item(**ItemFactory(pub_date=pub_date)))
            last = pub_date

        feed = Feed(**FeedFactory(items=items))

        assert scheduler.schedule(feed).days == pytest.approx(4)

    def test_regular_pattern(self):
        items = []
        last = timezone.now()

        for day in [3, 4] * 12:
            pub_date = last - timedelta(days=day)
            items.append(Item(**ItemFactory(pub_date=pub_date)))
            last = pub_date

        feed = Feed(**FeedFactory(items=items))

        assert scheduler.schedule(feed).days == pytest.approx(3)

    def test_min_frequency(self):
        now = timezone.now()
        feed = Feed(
            **FeedFactory(
                items=[
                    Item(
                        **ItemFactory(
                            pub_date=pub_date,
                        )
                    )
                    for pub_date in [
                        now - timedelta(seconds=1200 * i) for i in range(1, 12)
                    ]
                ],
            )
        )

        assert (scheduler.schedule(feed).total_seconds() / 3600) == pytest.approx(1)

    def test_rescheduled(self):
        now = timezone.now()
        feed = Feed(
            **FeedFactory(
                items=[
                    Item(
                        **ItemFactory(
                            pub_date=pub_date,
                        )
                    )
                    for pub_date in [now - timedelta(days=33 * i) for i in range(1, 12)]
                ],
            )
        )

        assert scheduler.schedule(feed).days == 33
