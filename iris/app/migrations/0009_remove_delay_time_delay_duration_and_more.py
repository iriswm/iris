# Generated by Django 4.1.1 on 2022-11-24 01:58

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("iris", "0008_alter_category_options_alter_commit_options_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="delay",
            old_name="time",
            new_name="duration",
        ),
        migrations.AlterField(
            model_name="delay",
            name="duration",
            field=models.DurationField(
                verbose_name="duration",
            ),
        ),
        migrations.AddField(
            model_name="suspension",
            name="lifted_at",
            field=models.DateTimeField(
                editable=False, null=True, verbose_name="lifted_at"
            ),
        ),
    ]