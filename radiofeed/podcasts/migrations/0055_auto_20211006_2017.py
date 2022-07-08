# Generated by Django 3.2.8 on 2021-10-06 20:17

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0054_podcast_podcasts_po_title_b6422d_idx"),
    ]

    operations = [
        migrations.AddField(
            model_name="podcast",
            name="queued",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="podcast",
            name="scheduled",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
