# Generated by Django 3.2.5 on 2021-07-17 16:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("podcasts", "0016_set_num_episodes"),
    ]

    operations = [
        migrations.RenameField(
            model_name="podcast",
            old_name="creators",
            new_name="owner",
        ),
    ]
