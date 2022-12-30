from __future__ import annotations

import datetime

import httpx
import pytest

from radiofeed.common import user_agent


class TestUserAgent:
    @pytest.fixture
    def mock_now(self, mocker):
        mocker.patch(
            "django.utils.timezone.now",
            return_value=datetime.datetime(year=2022, month=12, day=30),
        )

    def test_with_request(self, rf, mock_now):
        assert (
            user_agent.user_agent(rf.get("/"))
            == f"python-httpx/{httpx.__version__} (Radiofeed/2022-30-12; +http://testserver/)"
        )

    def test_with_site(self, db, mock_now):
        assert (
            user_agent.user_agent()
            == f"python-httpx/{httpx.__version__} (Radiofeed/2022-30-12; +http://example.com/)"
        )
