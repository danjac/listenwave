from __future__ import annotations

import base64
import dataclasses
import itertools
import re

from typing import Final, Iterator
from urllib.parse import urlparse

import httpx
import user_agent

from django.core.cache import cache

from radiofeed.common import batcher
from radiofeed.common.xml import xml_iterparse, xpath_finder
from radiofeed.podcasts.models import Podcast

_ITUNES_PODCAST_ID_RE: Final = re.compile(r"id(?P<id>\d+)")

_ITUNES_LOCATIONS: Final = (
    "de",
    "fi",
    "fr",
    "gb",
    "se",
    "us",
)


@dataclasses.dataclass(frozen=True)
class Feed:
    """Encapsulates iTunes API result.

    Attributes:
        rss: URL to RSS or Atom resource
        url: URL to website of podcast
        title: title of podcast
        image: URL to cover image
        podcast: matching Podcast instance in local database
    """

    rss: str
    url: str
    title: str = ""
    image: str = ""
    podcast: Podcast | None = None


def search_cached(search_term: str) -> list[Feed]:
    """Runs cached search for podcasts on iTunes API."""
    cache_key = "itunes:" + base64.urlsafe_b64encode(bytes(search_term, "utf-8")).hex()
    if (feeds := cache.get(cache_key)) is None:
        feeds = list(search(search_term))
        cache.set(cache_key, feeds)
    return feeds


def search(search_term: str) -> Iterator[Feed]:
    """Runs search for podcasts on iTunes API."""
    with _get_client() as client:
        return _parse_feeds(
            _get_response(
                client,
                "https://itunes.apple.com/search",
                {
                    "term": search_term,
                    "media": "podcast",
                },
            ).json()
        )


def crawl() -> Iterator[Feed]:
    """Crawls iTunes podcast catalog and creates new Podcast instances from any new feeds found."""
    for location in _ITUNES_LOCATIONS:
        yield from Crawler(location).crawl()


class Crawler:
    """Crawls iTunes podcast catalog.

    Args:
        location: country location e.g. "us"
    """

    def __init__(self, location: str):
        self._location = location
        self._feed_ids: set[str] = set()

    def crawl(self) -> Iterator[Feed]:
        """Crawls through location and finds new feeds, adding any new podcasts to the database."""
        with _get_client() as client:
            for url in self._parse_genre_urls(client):
                yield from self._parse_genre_url(client, url)

    def _parse_genre_urls(self, client: httpx.Client) -> Iterator[str]:
        return (
            href
            for href in self._parse_urls(
                _get_response(
                    client,
                    f"https://itunes.apple.com/{self._location}/genre/podcasts/id26",
                ).content
            )
            if href.startswith(
                f"https://podcasts.apple.com/{self._location}/genre/podcasts"
            )
        )

    def _parse_genre_url(self, client: httpx.Client, url: str) -> Iterator[Feed]:
        for feed_ids in batcher.batcher(self._parse_podcast_ids(client, url), 100):
            yield from self._parse_feeds(client, feed_ids)

    def _parse_feeds(self, client: httpx.Client, feed_ids: list[str]) -> Iterator[Feed]:
        _feed_ids: set[str] = set(feed_ids) - self._feed_ids

        yield from _parse_feeds(
            _get_response(
                client,
                "https://itunes.apple.com/lookup",
                {
                    "id": ",".join(_feed_ids),
                    "entity": "podcast",
                },
            ).json(),
        )

        self._feed_ids = self._feed_ids.union(_feed_ids)

    def _parse_podcast_ids(self, client: httpx.Client, url: str) -> Iterator[str]:
        return (
            podcast_id
            for podcast_id in (
                self._parse_podcast_id(href)
                for href in self._parse_urls(_get_response(client, url).content)
                if href.startswith(
                    f"https://podcasts.apple.com/{self._location}/podcast/"
                )
            )
            if podcast_id
        )

    def _parse_urls(self, content: bytes) -> Iterator[str]:
        for element in xml_iterparse(content, "{http://www.apple.com/itms/}html"):
            with xpath_finder(element) as finder:
                yield from finder.iter("//a//@href")

    def _parse_podcast_id(self, url: str) -> str | None:
        if match := _ITUNES_PODCAST_ID_RE.search(urlparse(url).path.split("/")[-1]):
            return match.group("id")
        return None


def _parse_feeds(json_data: dict) -> Iterator[Feed]:
    for batch in batcher.batcher(_build_feeds_from_json(json_data), 100):

        feeds_for_podcasts, feeds = itertools.tee(batch)

        podcasts = Podcast.objects.filter(
            rss__in={f.rss for f in feeds_for_podcasts}
        ).in_bulk(field_name="rss")

        feeds_for_insert, feeds = itertools.tee(
            (
                dataclasses.replace(feed, podcast=podcasts.get(feed.rss))
                for feed in feeds
            ),
        )

        Podcast.objects.bulk_create(
            (
                Podcast(title=feed.title, rss=feed.rss)
                for feed in feeds_for_insert
                if feed.podcast is None
            ),
            ignore_conflicts=True,
        )

        yield from feeds


def _get_response(
    client: httpx.Client, url: str, params: dict | None = None
) -> httpx.Response:
    response = client.get(url, params=params)
    response.raise_for_status()
    return response


def _get_client() -> httpx.Client:
    return httpx.Client(
        headers={"user-agent": user_agent.generate_user_agent()},
        follow_redirects=True,
        timeout=10,
    )


def _build_feeds_from_json(json_data: dict) -> Iterator[Feed]:
    for result in json_data.get("results", []):
        try:
            yield Feed(
                rss=result["feedUrl"],
                url=result["collectionViewUrl"],
                title=result["collectionName"],
                image=result["artworkUrl600"],
            )
        except KeyError:
            continue
