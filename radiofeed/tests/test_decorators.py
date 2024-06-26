import http

from django.http import HttpResponse
from django_htmx.middleware import HtmxDetails

from radiofeed.decorators import ajax_login_required, htmx_login_required
from radiofeed.users.models import User


@htmx_login_required
def htmx_view(request):
    return HttpResponse()


@ajax_login_required
def ajax_view(request):
    return HttpResponse()


class TestAjaxLoginRequired:
    def test_is_authenticated(self, rf):
        request = rf.get("/")
        request.user = User()
        response = ajax_view(request)
        assert response.status_code == http.HTTPStatus.OK

    def test_is_anonymous(self, rf, anonymous_user):
        request = rf.get("/")
        request.user = anonymous_user
        response = ajax_view(request)
        assert response.status_code == http.HTTPStatus.UNAUTHORIZED


class TestHtmxLoginRequired:
    def test_is_authenticated(self, rf):
        request = rf.get("/", HTTP_HX_REQUEST="true")
        request.user = User()
        request.htmx = HtmxDetails(request)
        response = htmx_view(request)
        assert response.status_code == http.HTTPStatus.OK

    def test_is_anonymous(self, rf, anonymous_user):
        request = rf.get(
            "/",
            HTTP_HX_REQUEST="true",
            HTTP_HX_CURRENT_URL="http://testserver/podcasts/",
        )
        request.user = anonymous_user
        request.htmx = HtmxDetails(request)
        response = htmx_view(request)
        assert response.url == "/account/login/?next=/podcasts/"
