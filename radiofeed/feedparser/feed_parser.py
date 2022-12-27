from __future__ import annotations

import functools
import hashlib

from typing import Iterator

import attrs
import httpx
import user_agent

from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.http import http_date, quote_etag

from radiofeed.common import batcher, tokenizer
from radiofeed.episodes.models import Episode
from radiofeed.feedparser import rss_parser, scheduler
from radiofeed.feedparser.date_parser import parse_date
from radiofeed.feedparser.models import Feed, Item
from radiofeed.podcasts.models import Category, Podcast

_ACCEPT_HEADER = ",".join(
    [
        "application/atom+xml",
        "application/rdf+xml",
        "application/rss+xml",
        "application/x-netcdf",
        "application/xml;q=0.9",
        "text/xml;q=0.2",
        "*/*;q=0.1",
    ]
)


class FeedParserError(ValueError):
    """Generic parser error."""


class NotModified(FeedParserError):
    """RSS feed has not been modified since last update."""


class Duplicate(FeedParserError):
    """Another identical podcast exists in the database."""


class Inaccessible(FeedParserError):
    """Content is no longer accesssible."""


def parse_feed(podcast: Podcast, client: httpx.Client) -> bool:
    """Parses podcast RSS feed."""
    return FeedParser(podcast).parse(client)


def make_content_hash(content: bytes) -> str:
    """Hashes RSS content."""
    return hashlib.sha256(content).hexdigest()


def get_client() -> httpx.Client:
    """Returns HTTP client."""
    return httpx.Client(
        headers={
            "Accept": _ACCEPT_HEADER,
            "User-Agent": user_agent.generate_user_agent(),
        },
        timeout=10,
        follow_redirects=True,
    )


@functools.lru_cache
def get_categories() -> dict[str, Category]:
    """Returns a cached dict of categories with lowercase names as key."""
    return {
        category.lowercase_name: category
        for category in Category.objects.annotate(lowercase_name=Lower("name"))
    }


class FeedParser:
    """Updates a Podcast instance with its RSS or Atom feed source."""

    _max_retries: int = 3

    _feed_attrs = attrs.fields(Feed)  # type: ignore
    _item_attrs = attrs.fields(Item)  # type: ignore

    def __init__(self, podcast: Podcast):
        self._podcast = podcast

    def parse(self, client: httpx.Client):
        """Updates Podcast instance with RSS or Atom feed source.

        Podcast details are updated and episodes created, updated or deleted accordingly.

        If a podcast is discontinued (e.g. there is a duplicate feed in the database, or the feed is marked as complete) then the podcast is set inactive.
        """
        try:
            response = self._get_response(client)
            content_hash = make_content_hash(response.content)

            if content_hash == self._podcast.content_hash:
                raise NotModified()

            if (
                Podcast.objects.exclude(pk=self._podcast.pk)
                .filter(Q(rss=response.url) | Q(content_hash=content_hash))
                .exists()
            ):
                raise Duplicate()

            try:
                feed = rss_parser.parse_rss(response.content)
            except rss_parser.RssParserError as e:
                raise FeedParserError from e

            active = not (feed.complete)
            categories, keywords = self._extract_categories(feed)

            with transaction.atomic():

                self._podcast_update(
                    active=active,
                    num_retries=0,
                    content_hash=content_hash,
                    keywords=keywords,
                    rss=response.url,
                    etag=response.headers.get("ETag", ""),
                    modified=parse_date(response.headers.get("Last-Modified")),
                    extracted_text=self._extract_text(feed),
                    frequency=scheduler.schedule(feed),
                    **attrs.asdict(
                        feed,
                        filter=attrs.filters.exclude(  # type: ignore
                            self._feed_attrs.categories,
                            self._feed_attrs.complete,
                            self._feed_attrs.items,
                        ),
                    ),
                )

                self._podcast.categories.set(categories)
                self._episode_updates(feed)

        except Exception as e:
            self._handle_exception(e)

    def _get_response(self, client: httpx.Client) -> httpx.Response:
        response = client.get(self._podcast.rss, headers=self._get_feed_headers())

        if response.is_redirect:
            raise NotModified()

        if response.is_client_error:
            raise Inaccessible()

        try:
            # check for any other http errors
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise FeedParserError from e

        return response

    def _get_feed_headers(self) -> dict[str, str]:
        headers = {}
        if self._podcast.etag:
            headers["If-None-Match"] = quote_etag(self._podcast.etag)
        if self._podcast.modified:
            headers["If-Modified-Since"] = http_date(self._podcast.modified.timestamp())
        return headers

    def _handle_exception(self, exc: Exception) -> None:

        # check if podcast should be discontinued and no longer updated.
        # if a parsing error (e.g. HTTP or RSS error) then increment the num_retries field.

        num_retries: int = self._podcast.num_retries
        active: bool = True

        match exc:

            case Inaccessible() | Duplicate():
                # podcast should be discontinued and no longer updated
                active = False

            case NotModified():
                # successful pull, so reset num_retries
                num_retries = 0

            case FeedParserError():
                # increment num_retries in case a temporary error
                num_retries += 1

            case _:
                # any other error: raise immediately without any DB updates
                raise exc

        # if number of errors exceeds threshold then deactivate the podcast
        active = active and num_retries < self._max_retries

        # if podcast is still active, reschedule next update check
        frequency = (
            scheduler.reschedule(
                self._podcast.pub_date,
                self._podcast.frequency,
            )
            if active
            else self._podcast.frequency
        )

        self._podcast_update(
            active=active, num_retries=num_retries, frequency=frequency
        )

        # re-raise original exception
        raise exc

    def _podcast_update(self, **fields) -> None:
        now = timezone.now()

        Podcast.objects.filter(pk=self._podcast.id).update(
            updated=now,
            parsed=now,
            **fields,
        )

    def _extract_categories(self, feed: Feed) -> tuple[list[Category], str]:

        categories: list[Category] = []
        keywords: str = ""

        if category_names := {c.casefold() for c in feed.categories}:
            categories_dct = get_categories()

            categories = [
                categories_dct[name]
                for name in category_names
                if name in categories_dct
            ]

            keywords = " ".join(
                [name for name in category_names if name not in categories_dct]
            )

        return categories, keywords

    def _extract_text(self, feed: Feed) -> str:
        text = " ".join(
            value
            for value in [
                feed.title,
                feed.description,
                feed.owner,
            ]
            + feed.categories
            + [item.title for item in feed.items][:6]
            if value
        )
        return " ".join(tokenizer.tokenize(self._podcast.language, text))

    def _episode_updates(self, feed: Feed) -> None:
        qs = Episode.objects.filter(podcast=self._podcast)

        # remove any episodes that may have been deleted on the podcast
        qs.exclude(guid__in={item.guid for item in feed.items}).delete()

        # determine new/current items based on presence of guid

        guids = dict(qs.values_list("guid", "pk"))

        # update existing content

        for batch in batcher.batcher(self._episodes_for_update(feed, guids), 1000):
            Episode.fast_update_objects.copy_update(
                batch,
                fields=[
                    "cover_url",
                    "description",
                    "duration",
                    "episode",
                    "episode_type",
                    "explicit",
                    "keywords",
                    "length",
                    "media_type",
                    "media_url",
                    "pub_date",
                    "season",
                    "title",
                ],
            )

        # add new episodes

        for batch in batcher.batcher(self._episodes_for_insert(feed, guids), 100):
            Episode.objects.bulk_create(batch, ignore_conflicts=True)

    def _episodes_for_insert(
        self, feed: Feed, guids: dict[str, int]
    ) -> Iterator[Episode]:
        return (
            self._make_episode(item) for item in feed.items if item.guid not in guids
        )

    def _episodes_for_update(
        self, feed: Feed, guids: dict[str, int]
    ) -> Iterator[Episode]:

        episode_ids = set()

        for item in (item for item in feed.items if item.guid in guids):
            if (episode_id := guids[item.guid]) not in episode_ids:
                yield self._make_episode(item, episode_id)
                episode_ids.add(episode_id)

    def _make_episode(self, item: Item, episode_id: int | None = None) -> Episode:
        return Episode(
            pk=episode_id,
            podcast=self._podcast,
            **attrs.asdict(
                item,
                filter=attrs.filters.exclude(  # type: ignore
                    self._item_attrs.categories,
                ),
            ),
        )
