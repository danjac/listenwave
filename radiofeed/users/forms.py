from collections.abc import Iterator

import lxml  # nosec
from django import forms

from radiofeed.podcasts.models import Podcast, Subscription
from radiofeed.users.models import User
from radiofeed.xml import XPathParser


class UserPreferencesForm(forms.ModelForm):
    """Form for user settings."""

    class Meta:
        model = User

        fields = ("send_email_notifications",)

        labels = {
            "send_email_notifications": "Send email notifications",
        }

        help_texts = {
            "send_email_notifications": "I'd like to receive notications of new content and recommendations."
        }


class OpmlUploadForm(forms.Form):
    """Form for uploading OPML into user collection."""

    opml = forms.FileField(
        label="Select OPML file",
        widget=forms.FileInput(
            attrs={
                "accept": ".opml,.xml,application/xml,text/x-opml,text/xml",
            }
        ),
    )

    _xpath_parser = XPathParser()

    def subscribe_to_feeds(self, user: User, limit: int = 360) -> int:
        """Subscribes user to feeds in uploaded OPML.

        Only active public feeds that already exist in the database will be included.

        Returns:
            number of subscribed feeds
        """

        if urls := set(self._parse_opml()) - set(
            Subscription.objects.filter(subscriber=user)
            .select_related("podcast")
            .values_list("podcast__rss", flat=True)
        ):
            podcasts = Podcast.objects.filter(
                active=True,
                private=False,
                rss__in=urls,
            )[:limit]

            return len(
                Subscription.objects.bulk_create(
                    [
                        Subscription(podcast=podcast, subscriber=user)
                        for podcast in podcasts.iterator()
                    ],
                    ignore_conflicts=True,
                )
            )

        return 0

    def _parse_opml(self) -> Iterator[str]:
        self.cleaned_data["opml"].seek(0)

        try:
            for element in self._xpath_parser.iterparse(
                self.cleaned_data["opml"].read(), "opml", "body"
            ):
                try:
                    yield from self._xpath_parser.iter(element, "//outline//@xmlUrl")
                finally:
                    element.clear()
        except lxml.etree.XMLSyntaxError:
            return
