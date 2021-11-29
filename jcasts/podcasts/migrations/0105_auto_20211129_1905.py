# Generated by Django 3.2.9 on 2021-11-29 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0104_remove_podcast_last_build_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="podcast",
            name="websub_exception",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="podcast",
            name="websub_hub",
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name="podcast",
            name="websub_lease",
            field=models.DurationField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="podcast",
            name="websub_mode",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name="podcast",
            name="websub_status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("requested", "Requested"),
                    ("active", "Active"),
                    ("inactive", "Inactive"),
                    ("error", "Error"),
                ],
                max_length=30,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="podcast",
            name="websub_status_changed",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="podcast",
            name="websub_token",
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name="podcast",
            name="websub_url",
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
