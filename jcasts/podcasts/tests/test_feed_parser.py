import http
import pathlib

from datetime import timedelta

import pytest
import requests

from django.utils import timezone

from jcasts.episodes.factories import EpisodeFactory
from jcasts.episodes.models import Episode
from jcasts.podcasts.date_parser import parse_date
from jcasts.podcasts.factories import (
    CategoryFactory,
    FeedFactory,
    FollowFactory,
    PodcastFactory,
)
from jcasts.podcasts.feed_parser import (
    get_categories_dict,
    get_feed_headers,
    get_frequency,
    is_feed_changed,
    parse_podcast_feed,
    reschedule,
    schedule_podcast_feeds,
)
from jcasts.podcasts.models import Podcast
from jcasts.podcasts.rss_parser import Feed


class MockResponse:
    def __init__(
        self,
        url="",
        status=http.HTTPStatus.OK,
        content=b"",
        headers=None,
        links=None,
    ):
        self.url = url
        self.content = content
        self.headers = headers or {}
        self.links = links or {}
        self.status_code = status

    def raise_for_status(self):
        ...


class BadMockResponse(MockResponse):
    def raise_for_status(self):
        raise requests.HTTPError(response=self)


class TestReschedule:
    def test_frequency_is_none(self):
        assert reschedule(None, 1.0) is None

    def test_frequency_not_none(self):
        scheduled = reschedule(timedelta(days=2), 2.0)
        assert ((scheduled - timezone.now()).total_seconds()) / 3600 == pytest.approx(
            96
        )


class TestGetFrequency:
    def get_frequency(self, dates):
        return get_frequency(dates).total_seconds() / 3600

    def test_get_frequency_no_pub_dates(self):
        assert get_frequency([]) is None

    def test_get_frequency(self):
        now = timezone.now()
        dates = [
            now - timedelta(days=3),
            now - timedelta(days=6),
            now - timedelta(days=9),
        ]

        assert self.get_frequency(dates) == pytest.approx(3 * 24)

    def test_get_frequency_max_value(self):
        now = timezone.now()
        dates = [
            now - timedelta(days=90),
            now - timedelta(days=200),
            now - timedelta(days=300),
        ]

        assert self.get_frequency(dates) == pytest.approx(30 * 24)

    def test_get_frequency_min_value(self):
        now = timezone.now()
        dates = [
            now - timedelta(hours=1),
            now - timedelta(hours=2),
            now - timedelta(hours=3),
        ]

        assert self.get_frequency(dates) == pytest.approx(3)


class TestIsFeedChanged:
    def test_feed_date_is_none(self):
        assert is_feed_changed(
            Podcast(last_build_date=timezone.now()),
            Feed(**FeedFactory(last_build_date=None)),
        )

    def test_podcast_date_is_none(self):
        assert is_feed_changed(
            Podcast(last_build_date=None),
            Feed(**FeedFactory(last_build_date=timezone.now())),
        )

    def test_different_podcast_and_feed_dates(self):
        now = timezone.now()
        assert is_feed_changed(
            Podcast(last_build_date=now - timedelta(days=3)),
            Feed(**FeedFactory(last_build_date=now)),
        )

    def test_same_podcast_and_feed_dates(self):
        now = timezone.now()
        assert not is_feed_changed(
            Podcast(last_build_date=now),
            Feed(**FeedFactory(last_build_date=now)),
        )


class TestFeedHeaders:
    def test_has_etag(self):
        podcast = Podcast(etag="abc123")
        headers = get_feed_headers(podcast)
        assert headers["If-None-Match"] == f'"{podcast.etag}"'

    def test_is_modified(self):
        podcast = Podcast(modified=timezone.now())
        headers = get_feed_headers(podcast)
        assert headers["If-Modified-Since"]


class TestSchedulePodcastFeeds:
    def test_schedule_podcast_feeds(self, db, mocker, mock_parse_podcast_feed):

        mocker.patch("multiprocessing.cpu_count", return_value=2)

        now = timezone.now()

        # inactive
        PodcastFactory(active=False)

        # too recent
        PodcastFactory(polled=now - timedelta(minutes=20))

        new = PodcastFactory(pub_date=None, polled=None)
        followed = FollowFactory(
            podcast__active=True, podcast__pub_date=now - timedelta(days=3)
        ).podcast
        promoted = PodcastFactory(
            active=True, promoted=True, pub_date=now - timedelta(days=4)
        )
        fresh = PodcastFactory(active=True, pub_date=now - timedelta(days=3))
        stale = PodcastFactory(active=True, pub_date=now - timedelta(days=99))

        schedule_podcast_feeds(frequency=timedelta(minutes=60))

        queued = Podcast.objects.filter(queued__isnull=False)
        assert queued.count() == 5

        assert len(mock_parse_podcast_feed.mock_calls) == 5

        for counter, podcast in enumerate(
            (
                followed,
                promoted,
                new,
                fresh,
                stale,
            )
        ):

            assert mock_parse_podcast_feed.mock_calls[counter][1][0] == podcast.id
            assert podcast in queued


class TestParsePodcastFeed:

    mock_file = "rss_mock.xml"
    mock_http_get = "requests.get"
    rss = "https://mysteriousuniverse.org/feed/podcast/"
    redirect_rss = "https://example.com/test.xml"
    updated = "Wed, 01 Jul 2020 15:25:26 +0000"

    @pytest.fixture
    def new_podcast(self, db):
        return PodcastFactory(cover_url=None, pub_date=None, queued=timezone.now())

    @pytest.fixture
    def categories(self, db):
        yield [
            CategoryFactory(name=name)
            for name in (
                "Philosophy",
                "Science",
                "Social Sciences",
                "Society & Culture",
                "Spirituality",
                "Religion & Spirituality",
            )
        ]

        get_categories_dict.cache_clear()

    def get_rss_content(self, filename=""):
        return open(
            pathlib.Path(__file__).parent / "mocks" / (filename or self.mock_file), "rb"
        ).read()

    def test_parse_no_podcasts(self, mocker, new_podcast, categories):
        mocker.patch(
            self.mock_http_get,
            return_value=MockResponse(
                url=new_podcast.rss,
                content=self.get_rss_content("rss_no_podcasts_mock.xml"),
            ),
        )

        result = parse_podcast_feed(new_podcast.id)
        assert not result
        with pytest.raises(ValueError):
            result.raise_exception()

        new_podcast.refresh_from_db()
        assert not new_podcast.active
        assert new_podcast.polled
        assert not new_podcast.queued
        assert new_podcast.result == Podcast.Result.INVALID_RSS

    def test_parse_empty_feed(self, mocker, new_podcast, categories):

        mocker.patch(
            self.mock_http_get,
            return_value=MockResponse(
                url=new_podcast.rss,
                content=self.get_rss_content("rss_empty_mock.xml"),
            ),
        )

        result = parse_podcast_feed(new_podcast.id)
        assert not result
        with pytest.raises(ValueError):
            result.raise_exception()

        new_podcast.refresh_from_db()
        assert not new_podcast.active
        assert new_podcast.polled
        assert not new_podcast.queued
        assert new_podcast.result == Podcast.Result.INVALID_RSS

    def test_parse_podcast_feed_podcast_not_found(self, db):
        result = parse_podcast_feed(1234)
        assert result.success is False

        with pytest.raises(Podcast.DoesNotExist):
            result.raise_exception()

    def test_parse_podcast_feed_ok(self, mocker, new_podcast, categories):

        episode_guid = "https://mysteriousuniverse.org/?p=168097"
        episode_title = "original title"

        # test updated
        EpisodeFactory(podcast=new_podcast, guid=episode_guid, title=episode_title)

        mocker.patch(
            self.mock_http_get,
            return_value=MockResponse(
                url=new_podcast.rss,
                content=self.get_rss_content(),
                headers={
                    "ETag": "abc123",
                    "Last-Modified": self.updated,
                },
            ),
        )
        assert parse_podcast_feed(new_podcast.id)

        # new episodes: 19
        assert Episode.objects.count() == 20

        # check episode updated
        episode = Episode.objects.get(guid=episode_guid)
        assert episode.title != episode_title

        new_podcast.refresh_from_db()

        assert new_podcast.rss
        assert new_podcast.active
        assert new_podcast.title == "Mysterious Universe"

        assert (
            new_podcast.description == "Blog and Podcast specializing in offbeat news"
        )

        assert new_podcast.owner == "8th Kind"

        assert new_podcast.modified
        assert new_podcast.modified.day == 1
        assert new_podcast.modified.month == 7
        assert new_podcast.modified.year == 2020
        assert not new_podcast.queued
        assert new_podcast.result == Podcast.Result.SUCCESS

        assert new_podcast.polled
        assert new_podcast.scheduled
        assert new_podcast.frequency_modifier == 1.0

        assert new_podcast.etag
        assert new_podcast.explicit
        assert new_podcast.cover_url

        assert new_podcast.pub_date == parse_date("Fri, 19 Jun 2020 16:58:03 +0000")

        assigned_categories = [c.name for c in new_podcast.categories.all()]

        assert "Science" in assigned_categories
        assert "Religion & Spirituality" in assigned_categories
        assert "Society & Culture" in assigned_categories
        assert "Philosophy" in assigned_categories

    def test_parse_podcast_same_last_build_date(self, mocker, new_podcast):

        new_podcast.last_build_date = parse_date("Wed, 01 Jul 2020 15:25:26 +0000")
        new_podcast.save()

        mocker.patch(
            self.mock_http_get,
            return_value=MockResponse(
                url=new_podcast.rss,
                content=self.get_rss_content(),
                headers={
                    "ETag": "abc123",
                    "Last-Modified": self.updated,
                },
            ),
        )
        assert not parse_podcast_feed(new_podcast.id)
        new_podcast.refresh_from_db()
        assert new_podcast.result == Podcast.Result.NOT_MODIFIED

    def test_parse_podcast_new_last_build_date(self, mocker, new_podcast, categories):

        new_podcast.last_build_date = parse_date("Tue, 30 Jun 2020 15:25:26 +0000")
        new_podcast.save()

        mocker.patch(
            self.mock_http_get,
            return_value=MockResponse(
                url=new_podcast.rss,
                content=self.get_rss_content(),
                headers={
                    "ETag": "abc123",
                    "Last-Modified": self.updated,
                },
            ),
        )
        assert parse_podcast_feed(new_podcast.id)

    def test_parse_podcast_last_build_date_none(self, mocker, new_podcast, categories):

        new_podcast.last_build_date = None
        new_podcast.save()

        mocker.patch(
            self.mock_http_get,
            return_value=MockResponse(
                url=new_podcast.rss,
                content=self.get_rss_content(),
                headers={
                    "ETag": "abc123",
                    "Last-Modified": self.updated,
                },
            ),
        )
        assert parse_podcast_feed(new_podcast.id)

    def test_parse_podcast_no_last_build_date(self, mocker, new_podcast, categories):

        new_podcast.last_build_date = parse_date("Tue, 30 Jun 2020 15:25:26 +0000")
        new_podcast.save()

        mocker.patch(
            self.mock_http_get,
            return_value=MockResponse(
                url=new_podcast.rss,
                content=self.get_rss_content("rss_mock_no_build_date.xml"),
                headers={
                    "ETag": "abc123",
                    "Last-Modified": self.updated,
                },
            ),
        )
        assert parse_podcast_feed(new_podcast.id)

    def test_parse_podcast_feed_permanent_redirect(
        self, mocker, new_podcast, categories
    ):
        mocker.patch(
            self.mock_http_get,
            return_value=MockResponse(
                url=self.redirect_rss,
                status=http.HTTPStatus.PERMANENT_REDIRECT,
                headers={
                    "ETag": "abc123",
                    "Last-Modified": self.updated,
                },
                content=self.get_rss_content(),
            ),
        )
        assert parse_podcast_feed(new_podcast.id)
        assert Episode.objects.filter(podcast=new_podcast).count() == 20

        new_podcast.refresh_from_db()

        assert new_podcast.rss == self.redirect_rss
        assert new_podcast.modified
        assert new_podcast.polled
        assert not new_podcast.queued

    def test_parse_podcast_feed_permanent_redirect_url_taken(
        self, mocker, new_podcast, categories
    ):
        other = PodcastFactory(rss=self.redirect_rss)
        current_rss = new_podcast.rss

        mocker.patch(
            self.mock_http_get,
            return_value=MockResponse(
                url=other.rss,
                status=http.HTTPStatus.PERMANENT_REDIRECT,
                headers={
                    "ETag": "abc123",
                    "Last-Modified": self.updated,
                },
                content=self.get_rss_content(),
            ),
        )
        assert not parse_podcast_feed(new_podcast.id)

        new_podcast.refresh_from_db()

        assert new_podcast.rss == current_rss
        assert not new_podcast.active
        assert new_podcast.polled
        assert not new_podcast.queued
        assert new_podcast.result == Podcast.Result.DUPLICATE_FEED

    def test_parse_podcast_feed_not_modified(self, mocker, new_podcast, categories):
        mocker.patch(
            self.mock_http_get,
            return_value=MockResponse(
                new_podcast.rss, status=http.HTTPStatus.NOT_MODIFIED
            ),
        )
        assert not parse_podcast_feed(new_podcast.id)

        new_podcast.refresh_from_db()
        assert new_podcast.active
        assert new_podcast.modified is None
        assert new_podcast.polled
        assert not new_podcast.queued
        assert new_podcast.result == Podcast.Result.NOT_MODIFIED

        assert new_podcast.scheduled
        assert new_podcast.frequency_modifier == 1.2

    def test_parse_podcast_feed_error(self, mocker, new_podcast, categories):
        mocker.patch(self.mock_http_get, side_effect=requests.RequestException)

        result = parse_podcast_feed(new_podcast.id)
        assert result.success is False

        with pytest.raises(requests.RequestException):
            result.raise_exception()

        new_podcast.refresh_from_db()
        assert new_podcast.active
        assert new_podcast.http_status is None
        assert new_podcast.polled
        assert not new_podcast.queued
        assert new_podcast.result == Podcast.Result.NETWORK_ERROR

    def test_parse_podcast_feed_http_gone(self, mocker, new_podcast, categories):
        mocker.patch(
            self.mock_http_get,
            return_value=BadMockResponse(status=http.HTTPStatus.GONE),
        )
        result = parse_podcast_feed(new_podcast.id)
        # no exception set for http errors
        result.raise_exception()

        assert result.success is False

        new_podcast.refresh_from_db()

        assert not new_podcast.active
        assert new_podcast.http_status == http.HTTPStatus.GONE
        assert new_podcast.polled
        assert not new_podcast.queued
        assert new_podcast.result == Podcast.Result.HTTP_ERROR

    def test_parse_podcast_feed_http_server_error(
        self, mocker, new_podcast, categories
    ):
        mocker.patch(
            self.mock_http_get,
            return_value=BadMockResponse(status=http.HTTPStatus.INTERNAL_SERVER_ERROR),
        )
        result = parse_podcast_feed(new_podcast.id)
        # no exception set for http errors
        result.raise_exception()

        assert result.success is False

        new_podcast.refresh_from_db()

        assert not new_podcast.active
        assert new_podcast.http_status == http.HTTPStatus.INTERNAL_SERVER_ERROR
        assert new_podcast.polled
        assert not new_podcast.queued
        assert new_podcast.result == Podcast.Result.HTTP_ERROR
