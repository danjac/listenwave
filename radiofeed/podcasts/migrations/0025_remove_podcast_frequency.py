# Generated by Django 3.2.5 on 2021-07-30 12:49

from __future__ import annotations

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0024_podcast_podcasts_po_schedul_e9ba7e_idx"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="podcast",
            name="frequency",
        ),
    ]
