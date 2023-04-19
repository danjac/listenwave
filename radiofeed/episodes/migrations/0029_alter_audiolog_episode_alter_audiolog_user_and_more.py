# Generated by Django 4.1 on 2022-08-27 09:53

from __future__ import annotations

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "podcasts",
            "0007_alter_podcast_categories_alter_subscription_podcast_and_more",
        ),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        (
            "episodes",
            "0001_squashed_0028_alter_audiolog_current_time_alter_audiolog_episode_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="audiolog",
            name="episode",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="audio_logs",
                to="episodes.episode",
                verbose_name="Episode",
            ),
        ),
        migrations.AlterField(
            model_name="audiolog",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="audio_logs",
                to=settings.AUTH_USER_MODEL,
                verbose_name="User",
            ),
        ),
        migrations.AlterField(
            model_name="bookmark",
            name="episode",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="bookmarks",
                to="episodes.episode",
                verbose_name="User",
            ),
        ),
        migrations.AlterField(
            model_name="bookmark",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="bookmarks",
                to=settings.AUTH_USER_MODEL,
                verbose_name="User",
            ),
        ),
        migrations.AlterField(
            model_name="episode",
            name="podcast",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="episodes",
                to="podcasts.podcast",
                verbose_name="Podcast",
            ),
        ),
    ]
