# Generated by Django 3.2.7 on 2021-09-18 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0038_auto_20210901_0726"),
    ]

    operations = [
        migrations.AddField(
            model_name="podcast",
            name="hub",
            field=models.URLField(blank=True, null=True),
        ),
    ]
