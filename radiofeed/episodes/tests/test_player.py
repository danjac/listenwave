from __future__ import annotations

import pytest

from radiofeed.episodes.player import Player


class TestPlayer:
    episode_id = 12345

    @pytest.fixture
    def req(self, rf):
        req = rf.get("/")
        req.session = {}
        return req

    @pytest.fixture
    def player(self, req):
        return Player(req)

    def test_get_if_none(self, player):
        assert player.get() is None

    def test_get_if_not_none(self, player):
        player.set(self.episode_id)
        assert player.get() == self.episode_id

    def test_pop_if_none(self, player):
        assert player.pop() is None

    def test_pop_if_not_none(self, player):
        player.set(self.episode_id)

        assert player.pop() == self.episode_id
        assert player.get() is None

    def test_has_false(self, player):
        assert self.episode_id not in player

    def test_has_true(self, player):
        player.set(self.episode_id)
        assert self.episode_id in player