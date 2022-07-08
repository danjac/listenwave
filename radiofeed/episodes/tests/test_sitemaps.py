from __future__ import annotations

from radiofeed.episodes.factories import EpisodeFactory


class TestEpisodeSitemap:
    def test_get(self, client, db, assert_ok):
        EpisodeFactory.create_batch(12)
        resp = client.get("/sitemap-episodes.xml")
        assert_ok(resp)
        assert resp["Content-Type"] == "application/xml"
