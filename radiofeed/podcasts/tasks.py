from huey.contrib.djhuey import db_task

from radiofeed.podcasts import emails, feed_updater
from radiofeed.podcasts.models import Podcast
from radiofeed.users.models import User


@db_task()
def feed_update(podcast_id):
    """Handles single podcast feed update.

    Args:
        podcast_id (int): Podcast PK

    Raises:
        PodcastDoesNotExist: if no active podcast found
    """
    feed_updater.FeedUpdater(Podcast.objects.get(pk=podcast_id, active=True)).update()


@db_task()
def send_recommendations_email(user_id):
    """Sends recommendation email to user.

    Args:
        user_id (int): User PK

    Raises:
        UserDoesNotExist: if no matching recipient user found
    """
    emails.send_recommendations_email(
        User.objects.email_notification_recipients().get(pk=user_id)
    )
