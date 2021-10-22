from datetime import timedelta

from django.core.management.base import BaseCommand

from jcasts.podcasts import feed_parser, podcastindex


class Command(BaseCommand):
    help = "Fetch recent feeds from Podcast Index"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
        )

        parser.add_argument(
            "--since", type=int, default=24, help="Hours since new feeds added"
        )

    def handle(self, *args, **options):
        feeds = podcastindex.recent_feeds(
            limit=options["limit"], since=timedelta(hours=options["since"])
        )
        for feed in feeds:
            self.stdout.write(f"{feed.title} [{feed.url}]")
            feed_parser.parse_podcast_feed(feed.url)

        self.stdout.write(self.style.SUCCESS(f"{len(feeds)} feed(s) updated"))
