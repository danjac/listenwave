# Generated by Django 3.2.6 on 2021-08-02 18:20

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("episodes", "0003_episode_cover_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="episode",
            name="episode",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="episode",
            name="episode_type",
            field=models.CharField(default="full", max_length=30),
        ),
        migrations.AddField(
            model_name="episode",
            name="season",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
