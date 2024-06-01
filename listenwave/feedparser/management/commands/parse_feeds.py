from concurrent.futures import wait

import djclick as click
import httpx
from django.db.models import Count, F, QuerySet

from listenwave.feedparser import feed_parser, scheduler
from listenwave.feedparser.exceptions import FeedParserError
from listenwave.http_client import get_client
from listenwave.podcasts.models import Podcast
from listenwave.thread_pool import DatabaseSafeThreadPoolExecutor


@click.command(help="Parses RSS feeds of all scheduled podcasts.")
@click.option("--limit", default=360, help="Number of feeds to process")
def command(limit: int) -> None:
    """Implementation of command."""

    client = get_client()

    with DatabaseSafeThreadPoolExecutor() as executor:
        wait(
            executor.db_safe_map(
                lambda podcast: _parse_feed(podcast, client),
                _get_scheduled_podcasts(limit),
            )
        )


def _get_scheduled_podcasts(limit: int) -> QuerySet[Podcast]:
    return (
        scheduler.get_scheduled_podcasts()
        .alias(subscribers=Count("subscriptions"))
        .filter(active=True)
        .order_by(
            F("subscribers").desc(),
            F("promoted").desc(),
            F("parsed").asc(nulls_first=True),
        )[:limit]
    )


def _parse_feed(podcast: Podcast, client: httpx.Client) -> None:
    try:
        feed_parser.parse_feed(podcast, client)
        click.echo(
            click.style(
                f"{podcast}: OK",
                bold=True,
                fg="green",
            )
        )
    except FeedParserError as exc:
        click.echo(
            click.style(
                f"{podcast}: {exc.parser_error.label}",  # type: ignore[union-attr]
                bold=True,
                fg="red",
            )
        )