# Generated by Django 3.2.9 on 2021-11-24 15:33

from __future__ import annotations

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0099_podcast_num_failures"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="podcast",
            name="frequency_modifier",
        ),
    ]
