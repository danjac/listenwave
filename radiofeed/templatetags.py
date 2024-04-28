from __future__ import annotations

import functools
import math
import urllib.parse
from typing import TYPE_CHECKING, Any, Final, TypedDict

from django import template
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.paginator import Page, Paginator
from django.core.signing import Signer
from django.shortcuts import resolve_url
from django.template.defaultfilters import pluralize
from django.templatetags.static import static
from django.urls import reverse
from django.utils.safestring import mark_safe

from radiofeed import cleaners

if TYPE_CHECKING:  # pragma: nocover
    from django.core.paginator import Page
    from django.db.models import QuerySet
    from django.template.context import RequestContext

ACCEPT_COOKIES_NAME: Final = "accept-cookies"

COVER_IMAGE_SIZES: Final = (100, 200, 300)

_SECONDS_IN_MINUTE: Final = 60
_SECONDS_IN_HOUR: Final = 3600

register = template.Library()


class ActiveLink(TypedDict):
    """Provides details on whether a link is currently active, along with its
    URL and CSS."""

    url: str
    css: str
    active: bool


@register.simple_tag(takes_context=True)
def active_link(
    context: RequestContext,
    to: Any,
    *,
    css: str = "link",
    active_css: str = "active",
    **kwargs,
) -> ActiveLink:
    """Returns url with active link info if matching URL."""
    url = resolve_url(to, **kwargs)
    return (
        ActiveLink(active=True, css=f"{css} {active_css}", url=url)
        if context.request.path == url
        else ActiveLink(active=False, css=css, url=url)
    )


@register.inclusion_tag("_markdown.html")
def markdown(value: str | None) -> dict:
    """Renders cleaned HTML/Markdown content."""
    return {"content": mark_safe(cleaners.clean_html(value or ""))}  # noqa: S308


@register.inclusion_tag("_cookie_notice.html", takes_context=True)
def cookie_notice(context: RequestContext) -> dict:
    """Renders GDPR cookie notice. Notice should be hidden once user has clicked
    "Accept Cookies" button."""
    return {"accept_cookies": ACCEPT_COOKIES_NAME in context.request.COOKIES}


@register.inclusion_tag("_search_form.html", takes_context=True)
def search_form(
    context: RequestContext,
    placeholder: str,
    search_url: str = "",
    clear_search_url: str = "",
) -> dict:
    """Renders search form component."""
    return {
        "placeholder": placeholder,
        "search_url": search_url or context.request.path,
        "clear_search_url": clear_search_url or context.request.path,
        "request": context.request,
    }


@register.simple_tag
@functools.cache
def get_cover_image_url(cover_url: str | None, size: int) -> str:
    """Returns signed cover image URL."""
    _assert_cover_size(size)
    if cover_url:
        return (
            reverse(
                "cover_image",
                kwargs={
                    "size": size,
                },
            )
            + "?"
            + urllib.parse.urlencode({"url": Signer().sign(cover_url)})
        )
    return ""


@register.simple_tag
@functools.cache
def get_placeholder_cover_url(size: int) -> str:
    """Return placeholder cover image URL."""
    _assert_cover_size(size)
    return static(f"img/placeholder-{size}.webp")


@register.inclusion_tag("_cover_image.html")
@functools.cache
def cover_image(
    cover_url: str | None,
    size: int,
    title: str,
    url: str = "",
    css_class: str = "",
) -> dict:
    """Renders a cover image with proxy URL."""

    return {
        "cover_url": get_cover_image_url(cover_url, size),
        "placeholder": get_placeholder_cover_url(size),
        "title": title,
        "size": size,
        "url": url,
        "css_class": css_class,
    }


@register.filter
def format_duration(total_seconds: int | None) -> str:
    """Formats duration (in seconds) as human readable value e.g. 1h 30min."""
    if total_seconds is None or total_seconds < _SECONDS_IN_MINUTE:
        return ""

    rv: list[str] = []

    if total_hours := math.floor(total_seconds / _SECONDS_IN_HOUR):
        rv.append(f"{total_hours} hour{pluralize(total_hours)}")

    if total_minutes := round((total_seconds % _SECONDS_IN_HOUR) / _SECONDS_IN_MINUTE):
        rv.append(f"{total_minutes} minute{pluralize(total_minutes)}")

    return " ".join(rv)


@register.simple_tag(takes_context=True)
def pagination_url(
    context: RequestContext, page_number: int, param: str = "page"
) -> str:
    """Returns URL for next/previous page."""
    qs = context.request.GET.copy()
    qs[param] = page_number
    return f"{context.request.path}?{qs.urlencode()}"


@register.simple_tag(takes_context=True)
def paginate(
    context: RequestContext,
    object_list: QuerySet,
    page_size: int = 30,
    param: str = "page",
    **kwargs,
) -> Page:
    """Returns paginated object list."""

    return Paginator(object_list, page_size).get_page(
        context.request.GET.get(param, ""), **kwargs
    )


@register.simple_tag
@functools.cache
def get_site() -> Site:
    """Returns the current Site instance. Use when `request.site` is unavailable, e.g. in emails run from cronjobs."""

    return Site.objects.get_current()


@register.simple_tag
def absolute_uri(to: Any | None = None, *args, **kwargs) -> str:
    """Returns the absolute URL to site domain."""

    site = get_site()
    path = resolve_url(to, *args, **kwargs) if to else ""
    scheme = "https" if settings.SECURE_SSL_REDIRECT else "http"

    return f"{scheme}://{site.domain}{path}"


def _assert_cover_size(size: int) -> None:
    assert size in COVER_IMAGE_SIZES, f"invalid cover image size:{size}"