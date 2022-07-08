# Generated by Django 3.2.6 on 2021-08-08 07:00

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0028_remove_podcast_exception"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="follow",
            name="uniq_follow",
        ),
        migrations.RemoveConstraint(
            model_name="recommendation",
            name="unique_recommendation",
        ),
        migrations.AddConstraint(
            model_name="follow",
            constraint=models.UniqueConstraint(fields=("user", "podcast"), name="unique_podcasts_follow"),
        ),
        migrations.AddConstraint(
            model_name="recommendation",
            constraint=models.UniqueConstraint(
                fields=("podcast", "recommended"), name="unique_podcasts_recommendation"
            ),
        ),
    ]
