# Generated by Django 4.1.5 on 2023-01-05 20:14

from __future__ import annotations

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0013_podcast_podcasts_po_content_736948_idx"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="category",
            name="name_en",
        ),
        migrations.RemoveField(
            model_name="category",
            name="name_fi",
        ),
    ]
