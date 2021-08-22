# Generated by Django 3.2.6 on 2021-08-22 07:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0034_auto_20210821_1502"),
    ]

    operations = [
        migrations.AddField(
            model_name="podcast",
            name="exception",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="podcast",
            name="http_status",
            field=models.SmallIntegerField(blank=True, null=True),
        ),
    ]
