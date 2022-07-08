# Generated by Django 3.2.8 on 2021-10-06 05:35

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0053_auto_20211005_1835"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="podcast",
            index=models.Index(fields=["title"], name="podcasts_po_title_b6422d_idx"),
        ),
    ]
