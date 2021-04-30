from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from audiotrails.users.factories import UserFactory

from ..factories import AudioLogFactory, EpisodeFactory
from ..models import AudioLog
from ..player import Player


class PlayerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.episode = EpisodeFactory()
        cls.user = UserFactory()

    def setUp(self):
        self.rf = RequestFactory()

    def test_start_episode(self):
        req = self.rf.get("/")
        req.session = {}
        req.user = self.user
        player = Player(req)

        self.assertEqual(player.start_episode(self.episode), 0)

        log = AudioLog.objects.get()

        self.assertEqual(log.episode, self.episode)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.current_time, 0)

        self.assertFalse(log.completed)
        self.assertTrue(log.updated)

        self.assertTrue(player.is_playing(self.episode))

    def test_start_episode_already_played(self):

        log = AudioLogFactory(episode=self.episode, user=self.user, current_time=500)

        req = self.rf.get("/")
        req.session = {}
        req.user = self.user
        player = Player(req)
        self.assertEqual(player.start_episode(self.episode), 500)

        log.refresh_from_db()

        self.assertEqual(log.episode, self.episode)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.current_time, 500)

        self.assertTrue(log.updated)
        self.assertFalse(log.completed)

        self.assertTrue(player.is_playing(self.episode))

    def test_stop_episode_empty(self):
        req = self.rf.get("/")
        req.session = {}
        req.user = self.user
        player = Player(req)
        self.assertEqual(player.stop_episode(), None)

    def test_stop_episode_not_in_session(self):

        AudioLogFactory(user=self.user)

        req = self.rf.get("/")
        req.session = {}
        req.user = self.user

        player = Player(req)

        self.assertEqual(player.stop_episode(), None)

    def test_stop_episode_in_session(self):

        log = AudioLogFactory(user=self.user)

        req = self.rf.get("/")
        req.session = {"player_episode": log.episode.id}
        req.user = self.user

        player = Player(req)

        self.assertEqual(player.stop_episode(), log.episode)
        self.assertFalse(player.is_playing(log.episode))

    def test_stop_episode_mark_complete(self):

        log = AudioLogFactory(user=self.user)

        req = self.rf.get("/")
        req.session = {"player_episode": log.episode.id}
        req.user = self.user

        player = Player(req)

        self.assertEqual(player.stop_episode(mark_completed=True), log.episode)
        self.assertFalse(player.is_playing(log.episode))

        log.refresh_from_db()
        self.assertTrue(log.completed)

    def test_update_current_time_not_playing(self):
        req = self.rf.get("/")

        req.session = {}
        req.user = self.user

        player = Player(req)
        player.update_current_time(600)
        self.assertEqual(AudioLog.objects.count(), 0)

    def test_update_current_time(self):

        log = AudioLogFactory(user=self.user, current_time=500)

        req = self.rf.get("/")

        req.session = {"player_episode": log.episode.id}
        req.user = self.user

        player = Player(req)
        player.update_current_time(600)

        log.refresh_from_db()
        self.assertEqual(log.current_time, 600)

    def test_get_player_info_anonymous(self):

        req = self.rf.get("/")
        req.session = {}
        req.user = AnonymousUser()
        player = Player(req)
        self.assertEqual(player.get_player_info(), {})

    def test_get_player_info_user_empty(self):

        req = self.rf.get("/")
        req.session = {}
        req.user = self.user
        player = Player(req)
        self.assertEqual(player.get_player_info(), {})

    def test_get_player_info(self):

        log = AudioLogFactory(user=self.user, current_time=100)

        req = self.rf.get("/")
        req.session = {"player_episode": log.episode.id}
        req.user = self.user
        player = Player(req)

        self.assertEqual(
            player.get_player_info(),
            {
                "current_time": 100,
                "episode": log.episode,
            },
        )
