import pytest
from django.urls import reverse

from radiofeed.podcasts.models import Category, ItunesSearch, Podcast, Recommendation
from radiofeed.podcasts.tests.factories import (
    CategoryFactory,
    ItunesSearchFactory,
    PodcastFactory,
    RecommendationFactory,
)


class TestItunesSearchManager:
    @pytest.mark.django_db()
    def test_get_or_create_from_search_new(self):
        search, created = ItunesSearch.objects.get_or_create_from_search("testing")
        assert search.search == "testing"
        assert created is True

    @pytest.mark.django_db()
    def test_get_or_create_from_search_exists(self):
        instance = ItunesSearchFactory()
        search, created = ItunesSearch.objects.get_or_create_from_search(
            instance.search
        )
        assert search.search == instance.search
        assert created is False


class TestItunesSearchModel:
    def test_str(self):
        assert str(ItunesSearch(search="testing")) == "testing"


class TestRecommendationManager:
    @pytest.mark.django_db()
    def test_bulk_delete(self):
        RecommendationFactory.create_batch(3)
        Recommendation.objects.bulk_delete()
        assert Recommendation.objects.count() == 0

    @pytest.mark.django_db()
    def test_with_relevance(self):
        RecommendationFactory(similarity=0.5, frequency=3)
        recommendation = Recommendation.objects.with_relevance().first()
        assert recommendation.relevance == 1.5


class TestRecommendationModel:
    def test_str(self):
        assert str(Recommendation(id=100)) == "Recommendation #100"


class TestCategoryManager:
    @pytest.fixture()
    def category(self):
        return CategoryFactory(name="testing")

    @pytest.mark.django_db()
    def test_search_empty(self, category):
        assert Category.objects.search("").count() == 0

    @pytest.mark.django_db()
    def test_search(self, category):
        assert Category.objects.search("testing").count() == 1


class TestCategoryModel:
    def test_slug(self):
        category = Category(name="Testing")
        assert category.slug == "testing"

    def test_str(self):
        category = Category(name="Testing")
        assert str(category) == "Testing"


class TestPodcastManager:
    @pytest.mark.django_db()
    def test_search(self):
        PodcastFactory(title="testing")
        assert Podcast.objects.search("testing").count() == 1

    @pytest.mark.django_db()
    def test_search_no_results(self):
        PodcastFactory(title="testing")
        assert Podcast.objects.search("random").count() == 0

    @pytest.mark.django_db()
    def test_search_partial(self):
        PodcastFactory(title="testing")
        assert Podcast.objects.search("test").count() == 1

    @pytest.mark.django_db()
    def test_search_owner(self):
        PodcastFactory(owner="tester")
        assert Podcast.objects.search("tester").count() == 1

    @pytest.mark.django_db()
    def test_search_keywords(self):
        PodcastFactory(keywords="test")
        assert Podcast.objects.search("test").count() == 1

    @pytest.mark.django_db()
    def test_search_if_empty(self):
        PodcastFactory(title="testing")
        assert Podcast.objects.search("").count() == 0

    @pytest.mark.django_db()
    def test_search_title_fallback(self):
        # usually "the" would be removed by stemmer
        PodcastFactory(title="the")
        podcasts = Podcast.objects.search("the")
        assert podcasts.count() == 1
        assert podcasts.first().exact_match == 1

    @pytest.mark.django_db()
    def test_compare_exact_and_partial_matches_in_search(self):
        PodcastFactory(title="the testing")
        PodcastFactory(title="testing")

        podcasts = Podcast.objects.search("testing").order_by("-exact_match")

        assert podcasts.count() == 2

        first = podcasts[0]
        second = podcasts[1]

        assert first.title == "testing"
        assert first.exact_match == 1

        assert second.title == "the testing"
        assert second.exact_match == 0


class TestPodcastModel:
    def test_str(self):
        assert str(Podcast(title="title")) == "title"

    def test_str_title_empty(self):
        rss = "https://example.com/rss.xml"
        assert str(Podcast(title="", rss=rss)) == rss

    def test_slug(self):
        assert Podcast(title="Testing").slug == "testing"

    def test_slug_if_title_empty(self):
        assert Podcast().slug == "no-title"

    def test_cleaned_title(self):
        podcast = Podcast(title="<b>Test &amp; Code")
        assert podcast.cleaned_title == "Test & Code"

    def test_cleaned_description(self):
        podcast = Podcast(description="<b>Test &amp; Code")
        assert podcast.cleaned_description == "Test & Code"

    @pytest.mark.django_db()
    def test_get_latest_episode_url(self, podcast):
        url = podcast.get_latest_episode_url()
        assert url == reverse(
            "podcasts:latest_episode",
            kwargs={
                "podcast_id": podcast.pk,
                "slug": podcast.slug,
            },
        )
