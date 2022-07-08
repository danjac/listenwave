# Generated by Django 3.2.8 on 2021-10-14 08:42

from __future__ import annotations

import django.db.models.functions.text

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0065_auto_20211013_0853"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="podcast",
            name="podcasts_po_title_b6422d_idx",
        ),
        migrations.AddIndex(
            model_name="podcast",
            index=models.Index(
                django.db.models.functions.text.Lower("title"),
                name="podcasts_podcast_title_lower",
            ),
        ),
    ]
