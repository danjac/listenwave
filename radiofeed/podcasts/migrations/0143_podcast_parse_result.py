# Generated by Django 4.0.5 on 2022-07-02 09:25

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0142_remove_podcast_queued"),
    ]

    operations = [
        migrations.AddField(
            model_name="podcast",
            name="parse_result",
            field=models.CharField(
                blank=True,
                choices=[
                    ("success", "Success"),
                    ("not_modified", "Not Modified"),
                    ("http_error", "HTTP Error"),
                    ("rss_parser_error", "RSS Parser Error"),
                    ("duplicate_feed", "Duplicate Feed"),
                ],
                max_length=30,
                null=True,
            ),
        ),
    ]
