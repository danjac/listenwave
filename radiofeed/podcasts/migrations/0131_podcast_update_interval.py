# Generated by Django 4.0.5 on 2022-06-08 08:17

from __future__ import annotations

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0130_remove_podcast_update_interval"),
    ]

    operations = [
        migrations.AddField(
            model_name="podcast",
            name="update_interval",
            field=models.DurationField(default=datetime.timedelta(seconds=3600)),
        ),
    ]
