# Generated by Django 4.1.3 on 2022-11-03 21:19

from __future__ import annotations

import datetime

import django.contrib.postgres.search
import django.core.validators
import django.db.models.deletion

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("podcasts", "0008_alter_recommendation_podcast_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="name",
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name="category",
            name="name_en",
            field=models.CharField(max_length=100, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="category",
            name="name_fi",
            field=models.CharField(max_length=100, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="category",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="children",
                to="podcasts.category",
            ),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="active",
            field=models.BooleanField(
                default=True,
                help_text="Inactive podcasts will no longer be updated from their RSS feeds.",
            ),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="categories",
            field=models.ManyToManyField(
                blank=True, related_name="podcasts", to="podcasts.category"
            ),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="content_hash",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="cover_url",
            field=models.URLField(blank=True, max_length=2083, null=True),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="created",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="etag",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="explicit",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="extracted_text",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="frequency",
            field=models.DurationField(default=datetime.timedelta(days=1)),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="funding_text",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="funding_url",
            field=models.URLField(blank=True, max_length=2083, null=True),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="http_status",
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="keywords",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="language",
            field=models.CharField(
                default="en",
                max_length=2,
                validators=[django.core.validators.MinLengthValidator(2)],
            ),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="link",
            field=models.URLField(blank=True, max_length=2083, null=True),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="modified",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="num_retries",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="owner",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="parse_result",
            field=models.CharField(
                blank=True,
                choices=[
                    ("success", "Success"),
                    ("complete", "Complete"),
                    ("not_modified", "Not Modified"),
                    ("http_error", "HTTP Error"),
                    ("rss_parser_error", "RSS Parser Error"),
                    ("duplicate_feed", "Duplicate Feed"),
                ],
                max_length=30,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="parsed",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="promoted",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="pub_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="recipients",
            field=models.ManyToManyField(
                blank=True,
                related_name="recommended_podcasts",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="rss",
            field=models.URLField(max_length=500, unique=True),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="search_vector",
            field=django.contrib.postgres.search.SearchVectorField(
                editable=False, null=True
            ),
        ),
        migrations.AlterField(
            model_name="podcast",
            name="title",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="recommendation",
            name="frequency",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="recommendation",
            name="podcast",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="recommendations",
                to="podcasts.podcast",
            ),
        ),
        migrations.AlterField(
            model_name="recommendation",
            name="recommended",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="similar",
                to="podcasts.podcast",
            ),
        ),
        migrations.AlterField(
            model_name="recommendation",
            name="similarity",
            field=models.DecimalField(
                blank=True, decimal_places=10, max_digits=100, null=True
            ),
        ),
        migrations.AlterField(
            model_name="subscription",
            name="podcast",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="subscriptions",
                to="podcasts.podcast",
            ),
        ),
        migrations.AlterField(
            model_name="subscription",
            name="subscriber",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="subscriptions",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]