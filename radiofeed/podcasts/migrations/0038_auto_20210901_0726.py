# Generated by Django 3.2.6 on 2021-09-01 07:26

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0037_podcast_queued"),
    ]

    operations = [
        migrations.AddField(
            model_name="podcast",
            name="funding_text",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="podcast",
            name="funding_url",
            field=models.URLField(blank=True, max_length=2083, null=True),
        ),
    ]
