# Generated by Django 4.1.1 on 2022-11-15 03:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("iris", "0002_remove_worker_picture_remove_worker_picture_height_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="commit",
            name="worker",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="commits",
                to="iris.worker",
            ),
        ),
        migrations.AlterField(
            model_name="delay",
            name="worker",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="delays",
                to="iris.worker",
            ),
        ),
        migrations.AlterField(
            model_name="priority",
            name="worker",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="priorities",
                to="iris.worker",
            ),
        ),
        migrations.AlterField(
            model_name="suspension",
            name="worker",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="suspensions",
                to="iris.worker",
            ),
        ),
    ]
