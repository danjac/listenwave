from __future__ import annotations

from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Exists, OuterRef, QuerySet
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from ratelimit.decorators import ratelimit

from radiofeed.common.decorators import ajax_login_required
from radiofeed.common.http import HttpResponseConflict
from radiofeed.common.pagination import render_pagination_response
from radiofeed.episodes.models import Episode
from radiofeed.podcasts import itunes
from radiofeed.podcasts.models import Category, Podcast, Recommendation, Subscription


@require_http_methods(["GET"])
def index(request: HttpRequest) -> HttpResponse:
    """Render default podcast home page.

    If user is authenticated will show their subscriptions (if any); otherwise shows all promoted podcasts.
    """
    subscribed = (
        frozenset(request.user.subscription_set.values_list("podcast", flat=True))
        if request.user.is_authenticated
        else frozenset()
    )

    promoted = "promoted" in request.GET or not subscribed

    podcasts = _get_podcasts().order_by("-pub_date").distinct()

    return render_pagination_response(
        request,
        (
            podcasts.filter(promoted=True)
            if promoted
            else podcasts.filter(pk__in=subscribed)
        ),
        "podcasts/index.html",
        "podcasts/pagination/podcasts.html",
        {
            "promoted": promoted,
            "has_subscriptions": bool(subscribed),
            "search_url": reverse("podcasts:search_podcasts"),
        },
    )


@require_http_methods(["GET"])
def search_podcasts(request: HttpRequest) -> HttpResponse:
    """Render search page. Redirects to index page if search is empty."""
    if not request.search:
        return HttpResponseRedirect(reverse("podcasts:index"))

    return render_pagination_response(
        request,
        (
            _get_podcasts()
            .search(request.search.value)
            .order_by(
                "-rank",
                "-pub_date",
            )
        ),
        "podcasts/search.html",
        "podcasts/pagination/podcasts.html",
    )


@ratelimit(key="ip", rate="20/m")
@require_http_methods(["GET"])
def search_itunes(request: HttpRequest) -> HttpResponse:
    """Render iTunes search page. Redirects to index page if search is empty."""
    if not request.search:
        return HttpResponseRedirect(reverse("podcasts:index"))

    feeds: list[itunes.Feed] = []

    try:
        feeds = itunes.search_cached(request.search.value)
    except itunes.ItunesException:
        messages.error(request, _("Sorry, an error occurred trying to access iTunes."))

    return TemplateResponse(
        request,
        "podcasts/itunes_search.html",
        {
            "feeds": feeds,
            "clear_search_url": reverse("podcasts:index"),
        },
    )


@require_http_methods(["GET"])
def latest_episode(
    request: HttpRequest, podcast_id: int, slug: str | None = None
) -> HttpResponse:
    """Redirects to the latest episode for a given podcast.

    Raises:
        Http404: podcast not found
    """
    if (
        episode := Episode.objects.filter(podcast=podcast_id)
        .order_by("-pub_date")
        .first()
    ) is None:
        raise Http404()

    return HttpResponseRedirect(episode.get_absolute_url())


@require_http_methods(["GET"])
def similar(
    request: HttpRequest,
    podcast_id: int,
    slug: str | None = None,
    limit: int = 12,
) -> HttpResponse:
    """List similar podcasts based on recommendations.

    Raises:
        Http404: podcast not found
    """
    podcast = _get_podcast_or_404(podcast_id)

    return TemplateResponse(
        request,
        "podcasts/similar.html",
        _podcast_detail_context(
            podcast,
            {
                "recommendations": (
                    Recommendation.objects.filter(podcast=podcast)
                    .select_related("recommended")
                    .order_by("-similarity", "-frequency")
                )[:limit]
            },
        ),
    )


@require_http_methods(["GET"])
def podcast_detail(
    request: HttpRequest, podcast_id: int, slug: str | None = None
) -> HttpResponse:
    """Render details for a single podcast.

    Raises:
        Http404: podcast not found
    """
    podcast = _get_podcast_or_404(podcast_id)

    return TemplateResponse(
        request,
        "podcasts/detail.html",
        _podcast_detail_context(
            podcast,
            {
                "is_subscribed": podcast.is_subscribed(request.user),
            },
        ),
    )


@require_http_methods(["GET"])
def episodes(
    request: HttpRequest,
    podcast_id: int,
    slug: str | None = None,
    target: str = "object-list",
) -> HttpResponse:
    """Render episodes for a single podcast.

    Raises:
        Http404: podcast not found
    """
    podcast = _get_podcast_or_404(podcast_id)

    newest_first = request.GET.get("o", "d") == "d"

    episodes = Episode.objects.filter(podcast=podcast).select_related("podcast")

    extra_context = {
        "is_podcast_detail": True,
        "newest_first": newest_first,
        "oldest_first": not (newest_first),
    }

    return render_pagination_response(
        request,
        (
            episodes.search(request.search.value).order_by("-rank", "-pub_date")
            if request.search
            else episodes.order_by("-pub_date" if newest_first else "pub_date")
        ),
        "podcasts/episodes.html",
        "episodes/pagination/episodes.html",
        target=target,
        extra_context=extra_context
        if request.htmx.target == target
        else _podcast_detail_context(podcast, extra_context),
    )


@require_http_methods(["GET"])
def category_list(request: HttpRequest) -> HttpResponse:
    """List all categories containing podcasts."""
    categories = (
        Category.objects.annotate(
            has_podcasts=Exists(_get_podcasts().filter(categories=OuterRef("pk")))
        )
        .filter(has_podcasts=True)
        .order_by("name")
    )

    if request.search:
        categories = categories.search(request.search.value)

    return TemplateResponse(
        request, "podcasts/categories.html", {"categories": categories}
    )


@require_http_methods(["GET"])
def category_detail(
    request: HttpRequest, category_id: int, slug: str | None = None
) -> HttpResponse:
    """Render individual podcast category along with its podcasts.

    Podcasts can also be searched.

    Raises:
        Http404: category not found
    """
    category = get_object_or_404(Category, pk=category_id)
    podcasts = _get_podcasts().filter(categories=category).distinct()

    podcasts = (
        podcasts.search(request.search.value).order_by(
            "-rank",
            "-pub_date",
        )
        if request.search
        else podcasts.order_by("-pub_date")
    )

    return render_pagination_response(
        request,
        podcasts,
        "podcasts/category_detail.html",
        "podcasts/pagination/podcasts.html",
        {"category": category},
    )


@require_http_methods(["POST"])
@ajax_login_required
def subscribe(request: HttpRequest, podcast_id: int) -> HttpResponse:
    """Subscribe a user to a podcast.

    Returns:
        returns HTTP CONFLICT if user is already subscribed to this podcast, otherwise returns the subscribe action as HTMX snippet.

    Raises:
        Http404: podcast not found
    """
    podcast = _get_podcast_or_404(podcast_id)

    try:
        Subscription.objects.create(user=request.user, podcast=podcast)
    except IntegrityError:
        return HttpResponseConflict()

    messages.success(request, _("You are now subscribed to this podcast"))

    return TemplateResponse(
        request,
        "podcasts/actions/subscribe.html",
        {
            "podcast": podcast,
            "is_subscribed": True,
        },
    )


@require_http_methods(["DELETE"])
@ajax_login_required
def unsubscribe(request: HttpRequest, podcast_id: int) -> HttpResponse:
    """Unsubscribe user from a podcast.

    Raises:
        Http404: podcast not found
    """
    podcast = _get_podcast_or_404(podcast_id)

    Subscription.objects.filter(podcast=podcast, user=request.user).delete()

    messages.info(request, _("You are no longer subscribed to this podcast"))

    return TemplateResponse(
        request,
        "podcasts/actions/subscribe.html",
        {
            "podcast": podcast,
            "is_subscribed": False,
        },
    )


def _get_podcasts() -> QuerySet[Podcast]:
    return Podcast.objects.filter(pub_date__isnull=False)


def _get_podcast_or_404(podcast_id: int) -> Podcast:
    return get_object_or_404(_get_podcasts(), pk=podcast_id)


def _podcast_detail_context(
    podcast: Podcast, extra_context: dict | None = None
) -> dict:
    return {
        "podcast": podcast,
        "has_similar": Recommendation.objects.filter(podcast=podcast).exists(),
        "num_episodes": Episode.objects.filter(podcast=podcast).count(),
    } | (extra_context or {})
