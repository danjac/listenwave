# Generated by Django 4.0.4 on 2022-05-16 06:51

from __future__ import annotations

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("episodes", "0026_remove_audiolog_episodes_au_updated_eb4a9e_idx_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="audiolog",
            name="completed",
        ),
    ]
