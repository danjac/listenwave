from __future__ import annotations

from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import QuerySet
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from ratelimit.decorators import ratelimit

from radiofeed.common.decorators import ajax_login_required
from radiofeed.common.http import HttpResponseConflict, HttpResponseNoContent
from radiofeed.common.pagination import render_pagination_response
from radiofeed.episodes.models import AudioLog, Bookmark, Episode
from radiofeed.podcasts.models import Podcast


@require_http_methods(["GET"])
def index(request: HttpRequest) -> HttpResponse:
    """List latest episodes from subscriptions if any, else latest episodes from promoted podcasts."""
    promoted = "promoted" in request.GET

    subscribed = (
        frozenset(request.user.subscription_set.values_list("podcast", flat=True))
        if request.user.is_authenticated
        else frozenset()
    )

    since = timezone.now() - timedelta(days=14)

    podcasts = Podcast.objects.filter(pub_date__gt=since)

    if subscribed and not promoted:
        podcasts = podcasts.filter(pk__in=subscribed)
    else:
        podcasts = podcasts.filter(promoted=True)

    episodes = (
        Episode.objects.filter(pub_date__gt=since)
        .select_related("podcast")
        .filter(
            podcast__in=set(podcasts.values_list("pk", flat=True)),
        )
        .order_by("-pub_date", "-id")
        .distinct()
    )

    return render_pagination_response(
        request,
        episodes,
        "episodes/index.html",
        "episodes/pagination/episodes.html",
        {
            "promoted": promoted,
            "has_subscriptions": bool(subscribed),
            "search_url": reverse("episodes:search_episodes"),
        },
    )


@require_http_methods(["GET"])
def search_episodes(request: HttpRequest) -> HttpResponse:
    """Search episodes. If search empty redirects to index page."""
    if not request.search:
        return HttpResponseRedirect(reverse("episodes:index"))

    episodes = (
        Episode.objects.select_related("podcast")
        .search(request.search.value)
        .order_by("-rank", "-pub_date")
    )

    return render_pagination_response(
        request,
        episodes,
        "episodes/search.html",
        "episodes/pagination/episodes.html",
    )


@require_http_methods(["GET"])
def episode_detail(
    request: HttpRequest, episode_id: int, slug: str | None = None
) -> HttpResponse:
    """Renders episode detail.

    Raises:
        Http404: episode not found
    """
    episode = _get_episode_with_current_time_or_404(
        request, episode_id, with_podcast=True
    )
    return TemplateResponse(
        request,
        "episodes/detail.html",
        {
            "episode": episode,
            "is_playing": request.player.has(episode.id),
            "is_bookmarked": episode.is_bookmarked(request.user),
            "next_episode": Episode.objects.get_next_episode(episode),
            "previous_episode": Episode.objects.get_previous_episode(episode),
        },
    )


@require_http_methods(["POST"])
@ajax_login_required
def start_player(request: HttpRequest, episode_id: int) -> HttpResponse:
    """Starts player. Creates new audio log if necessary and adds episode to player session tracker.

    Raises:
        Http404: episode not found
    """
    episode = _get_episode_or_404(episode_id, with_podcast=True)

    log, _ = AudioLog.objects.update_or_create(
        episode=episode,
        user=request.user,
        defaults={
            "listened": timezone.now(),
        },
    )

    request.player.set(episode.id)

    return _render_audio_player(
        request,
        episode,
        start_player=True,
        current_time=log.current_time,
        listened=log.listened,
    )


@require_http_methods(["POST"])
@ajax_login_required
def close_player(request: HttpRequest) -> HttpResponse:
    """Closes player. Removes episode to player session tracker.

    Raises:
        Http404: episode not found
    """
    if episode_id := request.player.pop():

        episode = _get_episode_with_current_time_or_404(request, episode_id)

        return _render_audio_player(
            request,
            episode,
            start_player=False,
            current_time=episode.current_time,
            listened=episode.listened,
        )

    return HttpResponse()


@ratelimit(key="ip", rate="20/m")
@require_http_methods(["POST"])
@ajax_login_required
def player_time_update(request: HttpRequest) -> HttpResponse:
    """Update current play time of episode.

    Time should be passed in POST as `current_time` integer value.

    Returns:
        HTTP BAD REQUEST if missing/invalid `current_time`, otherwise HTTP NO CONTENT.
    """
    if episode_id := request.player.get():
        try:

            AudioLog.objects.filter(episode=episode_id, user=request.user).update(
                current_time=int(request.POST["current_time"]),
                listened=timezone.now(),
            )

        except (KeyError, ValueError):
            return HttpResponseBadRequest()

    return HttpResponseNoContent()


@require_http_methods(["GET"])
@login_required
def history(request: HttpRequest) -> HttpResponse:
    """Renders user's listening history. User can also search history."""
    newest_first = request.GET.get("o", "d") == "d"

    logs = AudioLog.objects.filter(user=request.user).select_related(
        "episode", "episode__podcast"
    )

    if request.search:
        logs = logs.search(request.search.value).order_by("-rank", "-listened")
    else:
        logs = logs.order_by("-listened" if newest_first else "listened")

    return render_pagination_response(
        request,
        logs,
        "episodes/history.html",
        "episodes/pagination/history.html",
        {
            "newest_first": newest_first,
            "oldest_first": not (newest_first),
        },
    )


@require_http_methods(["DELETE"])
@ajax_login_required
def remove_audio_log(request: HttpRequest, episode_id: int) -> HttpResponse:
    """Removes audio log from user history and returns HTMX snippet.

    Raises:
        Http404 if episode not found
    """
    episode = _get_episode_or_404(episode_id)

    if not request.player.has(episode.id):
        AudioLog.objects.filter(user=request.user, episode=episode).delete()
        messages.info(request, _("Removed from History"))

    return TemplateResponse(
        request,
        "episodes/actions/history.html",
        {"episode": episode},
    )


@require_http_methods(["GET"])
@login_required
def bookmarks(request: HttpRequest) -> HttpResponse:
    """Renders user's bookmarks. User can also search their bookmarks."""
    bookmarks = Bookmark.objects.filter(user=request.user).select_related(
        "episode", "episode__podcast"
    )
    if request.search:
        bookmarks = bookmarks.search(request.search.value).order_by("-rank", "-created")

    else:
        bookmarks = bookmarks.order_by("-created")
    return render_pagination_response(
        request,
        bookmarks,
        "episodes/bookmarks.html",
        "episodes/pagination/bookmarks.html",
    )


@require_http_methods(["POST"])
@ajax_login_required
def add_bookmark(request: HttpRequest, episode_id: int) -> HttpResponse:
    """Add episode to bookmarks.

    Raises:
        Http404: episode not found
    """
    episode = _get_episode_or_404(episode_id)

    try:
        Bookmark.objects.create(episode=episode, user=request.user)
    except IntegrityError:
        return HttpResponseConflict()

    messages.success(request, _("Added to Bookmarks"))

    return _render_bookmark_action(request, episode, True)


@require_http_methods(["DELETE"])
@ajax_login_required
def remove_bookmark(request: HttpRequest, episode_id: int) -> HttpResponse:
    """Remove episode from bookmarks.

    Raises:
        Http404: episode not found
    """
    episode = _get_episode_or_404(episode_id)

    Bookmark.objects.filter(user=request.user, episode=episode).delete()

    messages.info(request, _("Removed from Bookmarks"))

    return _render_bookmark_action(request, episode, False)


def _get_episode_or_404(
    episode_id: int,
    *,
    with_podcast: bool = False,
    queryset: QuerySet[Episode] | None = None,
) -> Episode:
    qs = queryset or Episode.objects.all()
    if with_podcast:
        qs = qs.select_related("podcast")
    return get_object_or_404(qs, pk=episode_id)


def _get_episode_with_current_time_or_404(
    request: HttpRequest,
    episode_id: int,
    *,
    with_podcast: bool = False,
) -> Episode:

    return _get_episode_or_404(
        episode_id,
        with_podcast=with_podcast,
        queryset=Episode.objects.with_current_time(request.user),
    )


def _render_audio_player(
    request: HttpRequest,
    episode: Episode,
    *,
    start_player: bool,
    current_time: datetime | None,
    listened: datetime | None,
) -> TemplateResponse:
    return TemplateResponse(
        request,
        "episodes/player.html",
        {
            "episode": episode,
            "start_player": start_player,
            "is_playing": start_player,
            "current_time": current_time,
            "listened": listened,
        },
    )


def _render_bookmark_action(
    request: HttpRequest, episode: Episode, is_bookmarked: bool
) -> TemplateResponse:
    return TemplateResponse(
        request,
        "episodes/actions/bookmark.html",
        {
            "episode": episode,
            "is_bookmarked": is_bookmarked,
        },
    )
