# Generated by Django 4.0 on 2021-12-16 19:22

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("episodes", "0021_auto_20210922_1012"),
    ]

    operations = [
        migrations.AddField(
            model_name="episode",
            name="link",
            field=models.URLField(blank=True, max_length=2083, null=True),
        ),
    ]
