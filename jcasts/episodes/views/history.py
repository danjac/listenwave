from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from jcasts.episodes.models import AudioLog, Episode
from jcasts.episodes.views import get_episode_or_404
from jcasts.shared.decorators import ajax_login_required
from jcasts.shared.paginate import paginate


@require_http_methods(["GET"])
@login_required
def index(request: HttpRequest) -> HttpResponse:

    logs = (
        AudioLog.objects.filter(user=request.user)
        .select_related("episode", "episode__podcast")
        .order_by("-updated")
    )

    newest_first = request.GET.get("ordering", "desc") == "desc"

    if request.search:
        logs = logs.search(request.search.value).order_by("-rank", "-updated")
    else:
        logs = logs.order_by("-updated" if newest_first else "updated")

    return TemplateResponse(
        request,
        "episodes/history.html",
        {
            "page_obj": paginate(request, logs),
            "newest_first": newest_first,
            "oldest_first": not (newest_first),
        },
    )


@require_http_methods(["POST"])
@ajax_login_required
def mark_complete(request: HttpRequest, episode_id: int) -> HttpResponse:

    episode = get_episode_or_404(request, episode_id)

    if not request.player.has(episode.id):

        AudioLog.objects.filter(user=request.user, episode=episode).update(
            completed=timezone.now(), current_time=0
        )

        messages.success(request, "Episode marked complete")

    return render_audio_log_toggle(
        request,
        episode,
        listened=True,
        completed=True,
    )


@require_http_methods(["DELETE"])
@ajax_login_required
def remove_audio_log(request: HttpRequest, episode_id: int) -> HttpResponse:

    episode = get_episode_or_404(request, episode_id)

    if not request.player.has(episode.id):
        AudioLog.objects.filter(user=request.user, episode=episode).delete()
        messages.info(request, "Removed from History")

    return render_audio_log_toggle(request, episode)


def render_audio_log_toggle(
    request: HttpRequest,
    episode: Episode,
    listened: bool = False,
    completed: bool = False,
) -> HttpResponse:
    return TemplateResponse(
        request,
        "episodes/_audio_log_toggle.html",
        {
            "episode": episode,
            "listened": listened,
            "completed": completed,
        },
    )
