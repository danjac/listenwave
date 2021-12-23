# Generated by Django 4.0 on 2021-12-23 07:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_remove_user_autoplay"),
        ("podcasts", "0119_podcast_feed_queue"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Follow",
            new_name="Subscription",
        ),
        migrations.RemoveConstraint(
            model_name="subscription",
            name="unique_podcasts_follow",
        ),
        migrations.RemoveIndex(
            model_name="subscription",
            name="podcasts_fo_created_0c8c22_idx",
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(
                fields=["-created"], name="podcasts_su_created_55323d_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="subscription",
            constraint=models.UniqueConstraint(
                fields=("user", "podcast"), name="unique_podcasts_subscription"
            ),
        ),
    ]
