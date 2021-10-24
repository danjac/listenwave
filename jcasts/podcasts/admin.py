from __future__ import annotations

from django.conf import settings
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from jcasts.podcasts import feed_parser, models


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    ordering = ("name",)
    list_display = (
        "name",
        "parent",
    )
    search_fields = ("name",)


class ResultFilter(admin.SimpleListFilter):
    title = "result"
    parameter_name = "Result"

    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin
    ) -> tuple[tuple[str, str], ...]:

        return (("none", "None"),) + tuple(models.Podcast.Result.choices)

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        value = self.value()

        if value == "none":
            return queryset.filter(result=None)

        elif value:
            return queryset.filter(result=value)

        return queryset


class PubDateFilter(admin.SimpleListFilter):
    title = "Pub Date"
    parameter_name = "pub_date"

    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin
    ) -> tuple[tuple[str, str], ...]:
        return (
            ("yes", "With pub date"),
            ("no", "With no pub date"),
            ("fresh", f"Fresh (< {settings.FRESHNESS_THRESHOLD.days} days)"),
            ("stale", f"Stale (> {settings.FRESHNESS_THRESHOLD.days} days)"),
        )

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        value = self.value()
        if value == "yes":
            return queryset.published()
        if value == "no":
            return queryset.unpublished()
        if value == "fresh":
            return queryset.fresh()
        if value == "stale":
            return queryset.stale()
        return queryset


class PromotedFilter(admin.SimpleListFilter):
    title = "Promoted"
    parameter_name = "promoted"

    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin
    ) -> tuple[tuple[str, str], ...]:
        return (("yes", "Promoted"),)

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        value = self.value()
        if value == "yes":
            return queryset.filter(promoted=True)
        return queryset


class QueuedFilter(admin.SimpleListFilter):
    title = "Queued"
    parameter_name = "queued"

    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin
    ) -> tuple[tuple[str, str], ...]:
        return (("yes", "Queued"),)

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        value = self.value()
        if value == "yes":
            return queryset.filter(queued__isnull=False)
        return queryset


class FollowedFilter(admin.SimpleListFilter):
    title = "Followed"
    parameter_name = "followed"

    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin
    ) -> tuple[tuple[str, str], ...]:
        return (("yes", "Followed"),)

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        value = self.value()
        queryset = queryset.with_followed()
        if value == "yes":
            return queryset.filter(followed=True)
        return queryset


class ActiveFilter(admin.SimpleListFilter):
    title = "Active"
    parameter_name = "active"

    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin
    ) -> tuple[tuple[str, str], ...]:
        return (
            ("yes", "Active"),
            ("no", "Inactive"),
        )

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        value = self.value()
        if value == "yes":
            return queryset.filter(active=True)
        if value == "no":
            return queryset.filter(active=False)
        return queryset


@admin.register(models.Podcast)
class PodcastAdmin(admin.ModelAdmin):
    list_filter = (
        ActiveFilter,
        FollowedFilter,
        PromotedFilter,
        PubDateFilter,
        QueuedFilter,
        ResultFilter,
    )

    list_display = (
        "__str__",
        "source",
        "active",
        "promoted",
        "result",
        "pub_date",
        "polled",
    )

    list_editable = (
        "active",
        "promoted",
    )
    search_fields = ("title", "rss")

    raw_id_fields = ("recipients",)

    readonly_fields = (
        "polled",
        "queued",
        "last_build_date",
        "modified",
        "pub_date",
        "etag",
        "http_status",
        "result",
        "exception",
    )

    actions = (
        "parse_podcast_feeds",
        "reactivate_podcast_feeds",
    )

    @admin.action(description="Parse podcast feeds")
    def parse_podcast_feeds(self, request: HttpRequest, queryset: QuerySet) -> None:

        if queryset.filter(active=False).exists():

            self.message_user(
                request,
                "You cannot parse inactive feeds",
                messages.ERROR,
            )

            return

        num_feeds = queryset.count()

        for podcast in queryset.iterator():
            feed_parser.parse_podcast_feed.delay(podcast.id)

        self.message_user(
            request,
            f"{num_feeds} podcast(s) scheduled for update",
            messages.SUCCESS,
        )

    def source(self, obj: models.Podcast) -> str:
        return obj.get_domain()

    def get_ordering(self, request: HttpRequest) -> list[str]:
        return (
            []
            if request.GET.get("q")
            else [
                "-polled",
                "-pub_date",
            ]
        )
