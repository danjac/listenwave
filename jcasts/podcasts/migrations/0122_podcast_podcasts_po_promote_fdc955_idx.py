# Generated by Django 4.0.2 on 2022-02-21 18:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0121_remove_podcast_podcasts_podcast_title_lower"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="podcast",
            index=models.Index(
                fields=["promoted"], name="podcasts_po_promote_fdc955_idx"
            ),
        ),
    ]
