# Generated by Django 3.2.9 on 2021-11-16 13:30

import statistics

from datetime import timedelta

from django.db import migrations
from django.utils import timezone


def set_frequency(apps, schema_editor):
    model = apps.get_model("podcasts", "Podcast")
    episodes_model = apps.get_model("episodes", "Episode")

    now = timezone.now()

    earliest = now - timedelta(days=90)

    default_frequency = timedelta(days=1)
    max_frequency = timedelta(days=30)

    for_update = []

    for obj in model.objects.filter(pub_date__gt=earliest, active=True):

        pub_dates = list(
            episodes_model.objects.filter(podcast=obj)
            .order_by("-pub_date")
            .filter(pub_date__gt=earliest)
            .values_list("pub_date", flat=True)[:12]
        )
        if len(pub_dates) in (0, 1):
            obj.frequency = default_frequency

        else:
            intervals = []

            latest, *pub_dates = sorted(pub_dates, reverse=True)

            for pub_date in pub_dates:
                intervals.append((latest - pub_date).total_seconds())
                latest = pub_date

            obj.frequency = timedelta(seconds=statistics.mean(intervals))
            for_update.append(obj)

    for obj in model.objects.filter(pub_date__lte=earliest, active=True):
        obj.frequency = max_frequency
        for_update.append(obj)

    model.objects.bulk_update(for_update, fields=["frequency"])


def set_frequency_none(apps, schema_editor):
    apps.get_model("podcasts", "Podcast").objects.update(frequency=None)


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0090_podcast_frequency"),
    ]

    operations = [
        migrations.RunPython(
            set_frequency,
            set_frequency_none,
        )
    ]
