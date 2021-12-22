from django.urls import path

from jcasts.episodes.views import (
    bookmarks,
    episode_detail,
    history,
    index,
    player,
    queue,
    search_episodes,
)

app_name = "episodes"


urlpatterns = [
    path("new/", index, name="index"),
    path("search/episodes/", search_episodes, name="search_episodes"),
    path(
        "episodes/<int:episode_id>/<slug:slug>/",
        episode_detail,
        name="episode_detail",
    ),
    path("player/~reload/", player.reload_player, name="reload_player"),
    path(
        "player/<int:episode_id>/~start/",
        player.start_player,
        name="start_player",
    ),
    path(
        "player/~close/",
        player.close_player,
        name="close_player",
    ),
    path(
        "player/~next/",
        player.play_next_episode,
        name="play_next_episode",
    ),
    path(
        "player/~timeupdate/",
        player.player_time_update,
        name="player_time_update",
    ),
    path("history/", history.index, name="history"),
    path(
        "history/<int:episode_id>/~complete/",
        history.mark_complete,
        name="mark_complete",
    ),
    path(
        "history/<int:episode_id>/~remove/",
        history.remove_audio_log,
        name="remove_audio_log",
    ),
    path("bookmarks/", bookmarks.index, name="bookmarks"),
    path(
        "bookmarks/<int:episode_id>/~add/",
        bookmarks.add_bookmark,
        name="add_bookmark",
    ),
    path(
        "bookmarks/<int:episode_id>/~remove/",
        bookmarks.remove_bookmark,
        name="remove_bookmark",
    ),
    path("queue/", queue.index, name="queue"),
    path("queue/~move/", queue.move_queue_items, name="move_queue_items"),
    path(
        "queue/<int:episode_id>/~add/start/",
        queue.add_to_queue,
        name="add_to_queue_start",
        kwargs={
            "add_to_start": True,
        },
    ),
    path(
        "queue/<int:episode_id>/~add/end/",
        queue.add_to_queue,
        name="add_to_queue_end",
        kwargs={
            "add_to_start": False,
        },
    ),
    path(
        "queue/<int:episode_id>/~remove/",
        queue.remove_from_queue,
        name="remove_from_queue",
    ),
]
