# Generated by Django 3.2.9 on 2021-11-17 06:27

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0093_podcast_websub_exception"),
    ]

    operations = [
        migrations.AddField(
            model_name="podcast",
            name="websub_url",
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
