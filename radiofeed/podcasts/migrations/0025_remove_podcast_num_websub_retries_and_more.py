# Generated by Django 4.1.7 on 2023-03-20 10:22

from __future__ import annotations

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("podcasts", "0024_podcast_num_websub_retries"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="podcast",
            name="num_websub_retries",
        ),
        migrations.RemoveField(
            model_name="podcast",
            name="websub_expires",
        ),
        migrations.RemoveField(
            model_name="podcast",
            name="websub_hub",
        ),
        migrations.RemoveField(
            model_name="podcast",
            name="websub_mode",
        ),
        migrations.RemoveField(
            model_name="podcast",
            name="websub_secret",
        ),
    ]
