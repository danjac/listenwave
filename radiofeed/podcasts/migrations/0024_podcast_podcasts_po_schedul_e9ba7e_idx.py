# Generated by Django 3.2.5 on 2021-07-30 08:26

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0023_podcast_scheduled"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="podcast",
            index=models.Index(fields=["-scheduled"], name="podcasts_po_schedul_e9ba7e_idx"),
        ),
    ]
