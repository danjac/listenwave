# Generated by Django 3.2.3 on 2021-05-23 15:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0003_set_cover_image_date"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="podcast",
            name="cover_image_etag",
        ),
    ]
