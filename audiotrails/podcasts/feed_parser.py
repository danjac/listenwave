from __future__ import annotations

import functools
import io
import mimetypes
import os
import uuid

from datetime import datetime
from functools import lru_cache
from typing import Any, Callable
from urllib.parse import urlparse

import box
import feedparser
import requests

from django.core.exceptions import ValidationError
from django.core.files.images import ImageFile
from django.core.validators import validate_image_file_extension
from django.utils import timezone
from django.utils.encoding import force_str
from PIL import Image, UnidentifiedImageError
from PIL.Image import DecompressionBombError

from audiotrails.episodes.models import Episode
from audiotrails.podcasts.date_parser import parse_date
from audiotrails.podcasts.models import Category, Podcast
from audiotrails.podcasts.text_parser import extract_keywords

MAX_IMAGE_SIZE = 1000
THUMBNAIL_SIZE = 200


@lru_cache
def get_categories_dict() -> dict[str, Category]:
    return Category.objects.in_bulk(field_name="name")


def parse_feed(podcast: Podcast, src: str = "") -> list[Episode]:

    result = box.Box(
        feedparser.parse(
            src or podcast.rss,
            etag=podcast.etag,
            modified=podcast.pub_date,
        ),
        default_box=True,
    )

    if not (items := parse_items(result)):
        return []

    pub_date = first_date(
        result.feed.published,
        result.feed.updated,
        *[item.published for item in items],
    )

    if pub_date is None:
        return []

    sync_podcast(podcast, pub_date, result, items)
    return sync_episodes(podcast, items)


def fetch_cover_image(podcast: Podcast, feed: box.Box) -> ImageFile | None:

    if podcast.cover_image or not feed.image.href:
        return None

    try:
        return create_image_file(requests.get(feed.image.href, timeout=5, stream=True))
    except requests.RequestException:
        pass

    return None


def create_image_file(response: requests.Response) -> ImageFile | None:

    if (img := create_image_obj(response.content)) is None:
        return None

    image_file = ImageFile(img, name=make_filename(response))

    try:
        validate_image_file_extension(image_file)
    except ValidationError:
        return None

    return image_file


def sync_podcast(
    podcast: Podcast,
    pub_date: datetime,
    result: box.Box,
    items: list[box.Box],
) -> None:

    now = timezone.now()

    # timestamps
    podcast.last_updated = now
    podcast.pub_date = pub_date
    podcast.etag = first_str(result.etag)

    # description

    podcast.title = result.feed.title
    podcast.link = result.feed.link
    podcast.language = first_str(result.feed.language, "en")[:2]
    podcast.description = first_str(result.feed.content, result.feed.summary)

    podcast.explicit = first_bool(result.explicit)
    podcast.creators = parse_creators(result.feed)

    parse_categories(podcast, result.feed, items)

    # reset errors
    podcast.sync_error = ""
    podcast.num_retries = 0

    if image := fetch_cover_image(podcast, result.feed):
        podcast.cover_image = image
        podcast.cover_image_date = now

    podcast.save()


def sync_episodes(podcast: Podcast, items: list[box.Box]) -> list[Episode]:
    episodes = Episode.objects.filter(podcast=podcast)

    # remove any episodes that may have been deleted on the podcast
    episodes.exclude(guid__in=[item.id for item in items]).delete()
    guids = episodes.values_list("guid", flat=True)

    return Episode.objects.bulk_create(
        [make_episode(podcast, item) for item in items if item.id not in guids],
        ignore_conflicts=True,
    )


def make_episode(podcast: Podcast, item: box.Box) -> Episode:
    return Episode(
        podcast=podcast,
        guid=item.id,
        title=item.title,
        link=item.link,
        media_url=item.audio.href,
        media_type=item.audio.type,
        length=item.audio.length or None,
        explicit=first_bool(item.itunes_explicit),
        description=first_str(item.description, item.summary),
        duration=first_str(item.itunes_duration),
        pub_date=parse_date(item.published),
        keywords=" ".join(parse_tags(item)),
    )


def parse_tags(item: box.Box) -> list[str]:
    return [tag.term for tag in item.tags or []]


def parse_categories(podcast: Podcast, feed: box.Box, items: list[box.Box]) -> None:
    """Extract keywords from text content for recommender
    and map to categories"""
    categories_dct = get_categories_dict()
    tags = parse_tags(feed)

    categories = [categories_dct[name] for name in tags if name in categories_dct]

    podcast.keywords = " ".join(name for name in tags if name not in categories_dct)
    podcast.extracted_text = extract_text(podcast, categories, items)
    podcast.categories.set(categories)  # type: ignore


def extract_text(
    podcast: Podcast,
    categories: list[Category],
    items: list[box.Box],
) -> str:
    text = " ".join(
        [
            podcast.title,
            podcast.description,
            podcast.keywords,
            podcast.creators,
        ]
        + [c.name for c in categories]
        + [item.title for item in items][:6]
    )
    return " ".join(extract_keywords(podcast.language, text))


def make_filename(response: requests.Response) -> str:
    _, ext = os.path.splitext(urlparse(response.url).path)

    if ext is None:
        try:
            content_type = response.headers["Content-Type"].split(";")[0]
        except KeyError:
            content_type = mimetypes.guess_type(response.url)[0] or ""

        ext = mimetypes.guess_extension(content_type) or ""

    return uuid.uuid4().hex + ext


def create_image_obj(raw: bytes) -> Image:
    try:
        img = Image.open(io.BytesIO(raw))

        if img.height > MAX_IMAGE_SIZE or img.width > MAX_IMAGE_SIZE:
            img = img.resize((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.ANTIALIAS)

        # remove Alpha channel
        img = img.convert("RGB")

        fp = io.BytesIO()
        img.seek(0)
        img.save(fp, "PNG")

        return fp

    except (
        DecompressionBombError,
        UnidentifiedImageError,
    ):
        return None


def parse_items(result: box.Box) -> list[box.Box]:
    return [
        item for item in [with_audio(item) for item in result.entries] if item.audio
    ]


def parse_creators(feed: box.Box) -> str:
    return " ".join({author.name for author in feed.authors if author.name})


def with_audio(
    item: box.Box,
) -> box.Box:
    for link in (item.links or []) + (item.enclosures or []):
        if is_audio(link):
            return item + box.Box(audio=link)
    return item


def is_audio(link: box.Box) -> bool:
    return link.type.startswith("audio/") and link.href and link.rel == "enclosure"


def first(*values: Any, convert: Callable, default=None) -> Any:
    """Returns first non-falsy value, converting the item."""
    for value in values:
        if value:
            return convert(value)
    return default


first_str = functools.partial(first, convert=force_str, default="")
first_date = functools.partial(first, convert=parse_date, default=None)
first_bool = functools.partial(first, convert=bool, default=False)
