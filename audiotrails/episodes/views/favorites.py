from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_POST, require_safe

from audiotrails.shared.decorators import ajax_login_required
from audiotrails.shared.pagination import render_paginated_response
from audiotrails.shared.response import HttpResponseNoContent

from ..models import Favorite
from . import get_episode_or_404


@require_safe
@login_required
def index(request: HttpRequest) -> HttpResponse:
    favorites = Favorite.objects.filter(user=request.user).select_related(
        "episode", "episode__podcast"
    )
    if request.search:
        favorites = favorites.search(request.search).order_by("-rank", "-created")
    else:
        favorites = favorites.order_by("-created")

    return render_paginated_response(
        request,
        favorites,
        "episodes/favorites.html",
        "episodes/_favorites.html",
    )


@require_POST
@ajax_login_required
def add_favorite(request: HttpRequest, episode_id: int) -> HttpResponse:
    episode = get_episode_or_404(request, episode_id, with_podcast=True)

    try:
        Favorite.objects.create(episode=episode, user=request.user)
    except IntegrityError:
        pass

    return HttpResponseNoContent()


@require_POST
@ajax_login_required
def remove_favorite(request: HttpRequest, episode_id: int) -> HttpResponse:
    episode = get_episode_or_404(request, episode_id)

    Favorite.objects.filter(user=request.user, episode=episode).delete()

    response = HttpResponseNoContent()
    response["HX-Trigger"] = "reload-favorites"
    return response
