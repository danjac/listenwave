from __future__ import annotations

from radiofeed.podcasts.models import Podcast, Recommendation
from radiofeed.users.emails import send_user_notification_email
from radiofeed.users.models import User


def send_recommendations_email(user: User) -> None:

    recommendations = (
        Recommendation.objects.for_user(user)
        .order_by("-frequency", "-similarity")
        .values_list("recommended", flat=True)
    )

    podcasts = Podcast.objects.filter(pk__in=list(recommendations)).distinct()[:3]

    if len(podcasts) not in range(2, 4):
        return

    # save recommendations

    if podcasts:
        user.recommended_podcasts.add(*podcasts)

    send_user_notification_email(
        user,
        f"Hi {user.username}, here are some new podcasts you might like!",
        "podcasts/emails/recommendations.txt",
        "podcasts/emails/recommendations.html",
        {
            "podcasts": podcasts,
        },
    )
