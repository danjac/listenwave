import hashlib
import hmac
import http
import traceback
import uuid

import attr
import requests

from django.db.models import Q
from django.http import HttpRequest
from django.utils import timezone
from django_rq import job

from jcasts.websub.models import Subscription

DEFAULT_LEASE_SECONDS = 24 * 60 * 60 * 7
MAX_BODY_SIZE = 1024 ** 2


@attr.s(kw_only=True)
class SubscribeResult:
    subscription_id: uuid.UUID = attr.ib()
    success: bool = attr.ib()
    status: int | None = attr.ib(default=None)
    exception: Exception | None = attr.ib(default=None)

    def __bool__(self) -> bool:
        return self.success


def renew():
    """Check any expired subscriptions and attempt to re-subscribe. This can be run
    in a cronjob."""

    for subscription in Subscription.objects.filter(
        status=Subscription.Status.SUBSCRIBED, expires__lt=timezone.now()
    ):
        subscribe.delay(subscription.id, mode="subscribe")


@job("default")
def subscribe(
    subscription_id: uuid.UUID,
    mode: str = "subscribe",
) -> SubscribeResult:
    """Attempt to send a subscribe or other request to the hub."""

    now = timezone.now()
    qs = Subscription.objects.filter(podcast__active=True)

    if mode == "subscribe":
        qs = qs.filter(
            Q(status__isnull=True)
            | Q(status=Subscription.Status.SUBSCRIBED, expires__lt=now)
        )

    try:
        subscription = qs.get(pk=subscription_id)
    except Subscription.DoesNotExist as e:
        return SubscribeResult(
            subscription_id=subscription_id,
            exception=e,
            success=False,
        )

    response = requests.post(
        subscription.hub,
        {
            "hub.mode": mode,
            "hub.topic": subscription.topic,
            "hub.secret": subscription.secret.hex,
            "hub.callback": subscription.get_callback_url(),
            "hub.lease_seconds": DEFAULT_LEASE_SECONDS,
        },
    )

    try:
        response.raise_for_status()

        # a 202 indicates the hub will try to verify asynchronously
        # through a GET request to the websub callback url. Otherwise we can set
        # relevant status immediately.

        subscription.status = (
            Subscription.Status.ACCEPTED
            if response.status_code == http.HTTPStatus.ACCEPTED
            else status_for_mode(mode)
        )

        subscription.status_changed = now
        subscription.exception = ""

    except requests.RequestException as e:

        subscription.exception = traceback.format_exc()

        return SubscribeResult(
            subscription_id=subscription.id,
            status=e.response.status_code if e.response else None,
            success=False,
            exception=e,
        )
    finally:
        subscription.save()

    return SubscribeResult(
        subscription_id=subscription.id,
        status=response.status_code,
        success=True,
    )


def status_for_mode(mode: str) -> str:
    return {
        "subscribe": Subscription.Status.SUBSCRIBED,
        "unsubscribe": Subscription.Status.UNSUBSCRIBED,
        "denied": Subscription.Status.DENIED,
    }[
        mode
    ]  # type:ignore


def check_signature(request: HttpRequest, subscription: Subscription) -> bool:

    try:
        print(request.META)
        if int(request.META["CONTENT_LENGTH"]) > MAX_BODY_SIZE:
            return False

        algo, signature = request.headers["X-Hub-Signature"].split("=")
        digest = hmac.new(
            subscription.secret.hex.encode("utf-8"),
            request.body,
            getattr(hashlib, algo),
        ).hexdigest()

    except (AttributeError, KeyError, ValueError):
        return False

    return hmac.compare_digest(signature, digest)
