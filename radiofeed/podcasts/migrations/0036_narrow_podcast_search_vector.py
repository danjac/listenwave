# Generated by Django 3.2.6 on 2021-08-26 09:41

from __future__ import annotations

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0035_auto_20210822_0748"),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP TRIGGER IF EXISTS podcast_update_search_trigger ON podcasts_podcast;"
            "CREATE TRIGGER podcast_update_search_trigger "
            "BEFORE INSERT OR UPDATE OF title, owner, search_vector "
            "ON podcasts_podcast "
            "FOR EACH ROW EXECUTE PROCEDURE "
            "tsvector_update_trigger("
            "search_vector, 'pg_catalog.english', title, owner);"
            "UPDATE podcasts_podcast SET search_vector = NULL;",
            reverse_sql="DROP TRIGGER IF EXISTS podcast_update_search_trigger ON podcasts_podcast;",
        ),
    ]
