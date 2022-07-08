from __future__ import annotations

from huey.contrib.djhuey import db_task

from radiofeed.feedparser.feed_parser import FeedParser
from radiofeed.podcasts.models import Podcast


@db_task()
def parse_feed(podcast_id: int) -> None:
    """Handles single podcast feed update.

    Raises:
        PodcastDoesNotExist: if no podcast found
    """
    FeedParser(Podcast.objects.get(pk=podcast_id)).parse()
