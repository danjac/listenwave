# Generated by Django 4.0.4 on 2022-05-19 19:33

from __future__ import annotations

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0126_podcast_refresh_interval"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="podcast",
            name="refresh_interval",
        ),
    ]
