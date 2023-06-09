# Generated by Django 4.1.1 on 2022-11-23 13:45

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("iris", "0007_work_has_priority"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="category",
            options={"verbose_name": "category", "verbose_name_plural": "categories"},
        ),
        migrations.AlterModelOptions(
            name="commit",
            options={"verbose_name": "commit", "verbose_name_plural": "commits"},
        ),
        migrations.AlterModelOptions(
            name="delay",
            options={"verbose_name": "delay", "verbose_name_plural": "delays"},
        ),
        migrations.AlterModelOptions(
            name="job",
            options={"verbose_name": "job", "verbose_name_plural": "jobs"},
        ),
        migrations.AlterModelOptions(
            name="notetemplate",
            options={
                "verbose_name": "note template",
                "verbose_name_plural": "note templates",
            },
        ),
        migrations.AlterModelOptions(
            name="station",
            options={"verbose_name": "station", "verbose_name_plural": "stations"},
        ),
        migrations.AlterModelOptions(
            name="suspension",
            options={
                "verbose_name": "suspension",
                "verbose_name_plural": "suspensions",
            },
        ),
        migrations.AlterModelOptions(
            name="task",
            options={"verbose_name": "task", "verbose_name_plural": "tasks"},
        ),
        migrations.AlterModelOptions(
            name="taskconsolidation",
            options={
                "verbose_name": "task consolidation",
                "verbose_name_plural": "task consolidations",
            },
        ),
        migrations.AlterModelOptions(
            name="taskspawn",
            options={
                "verbose_name": "task spawn",
                "verbose_name_plural": "task spawns",
            },
        ),
        migrations.AlterModelOptions(
            name="work",
            options={"verbose_name": "work", "verbose_name_plural": "works"},
        ),
        migrations.AlterModelOptions(
            name="worker",
            options={"verbose_name": "worker", "verbose_name_plural": "workers"},
        ),
        migrations.AlterField(
            model_name="category",
            name="name",
            field=models.CharField(max_length=64, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="category",
            name="spawned_tasks",
            field=models.ManyToManyField(
                related_name="spawned_by_categories",
                through="iris.CategorySpawnedTasks",
                to="iris.task",
                verbose_name="spawned tasks",
            ),
        ),
        migrations.AlterField(
            model_name="commit",
            name="created",
            field=models.DateTimeField(auto_now_add=True, verbose_name="created"),
        ),
        migrations.AlterField(
            model_name="commit",
            name="job",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                to="iris.job",
                verbose_name="job",
            ),
        ),
        migrations.AlterField(
            model_name="commit",
            name="modified",
            field=models.DateTimeField(auto_now=True, verbose_name="modified"),
        ),
        migrations.AlterField(
            model_name="commit",
            name="notes",
            field=models.TextField(blank=True, verbose_name="notes"),
        ),
        migrations.AlterField(
            model_name="commit",
            name="worker",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="commits",
                to="iris.worker",
                verbose_name="worker",
            ),
        ),
        migrations.AlterField(
            model_name="delay",
            name="created",
            field=models.DateTimeField(auto_now_add=True, verbose_name="created"),
        ),
        migrations.AlterField(
            model_name="delay",
            name="job",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="delays",
                to="iris.job",
                verbose_name="job",
            ),
        ),
        migrations.AlterField(
            model_name="delay",
            name="modified",
            field=models.DateTimeField(auto_now=True, verbose_name="modified"),
        ),
        migrations.AlterField(
            model_name="delay",
            name="notes",
            field=models.TextField(blank=True, verbose_name="notes"),
        ),
        migrations.AlterField(
            model_name="delay",
            name="time",
            field=models.DurationField(verbose_name="time"),
        ),
        migrations.AlterField(
            model_name="delay",
            name="worker",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="delays",
                to="iris.worker",
                verbose_name="worker",
            ),
        ),
        migrations.AlterField(
            model_name="job",
            name="created",
            field=models.DateTimeField(auto_now_add=True, verbose_name="created"),
        ),
        migrations.AlterField(
            model_name="job",
            name="modified",
            field=models.DateTimeField(auto_now=True, verbose_name="modified"),
        ),
        migrations.AlterField(
            model_name="job",
            name="task",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="jobs",
                to="iris.task",
                verbose_name="task",
            ),
        ),
        migrations.AlterField(
            model_name="job",
            name="work",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="jobs",
                to="iris.work",
                verbose_name="work",
            ),
        ),
        migrations.AlterField(
            model_name="notetemplate",
            name="path",
            field=models.CharField(max_length=64, verbose_name="path"),
        ),
        migrations.AlterField(
            model_name="notetemplate",
            name="template",
            field=models.CharField(max_length=256, verbose_name="template"),
        ),
        migrations.AlterField(
            model_name="station",
            name="name",
            field=models.CharField(max_length=64, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="suspension",
            name="created",
            field=models.DateTimeField(auto_now_add=True, verbose_name="created"),
        ),
        migrations.AlterField(
            model_name="suspension",
            name="job",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="suspensions",
                to="iris.job",
                verbose_name="job",
            ),
        ),
        migrations.AlterField(
            model_name="suspension",
            name="modified",
            field=models.DateTimeField(auto_now=True, verbose_name="modified"),
        ),
        migrations.AlterField(
            model_name="suspension",
            name="notes",
            field=models.TextField(blank=True, verbose_name="notes"),
        ),
        migrations.AlterField(
            model_name="suspension",
            name="worker",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="suspensions",
                to="iris.worker",
                verbose_name="worker",
            ),
        ),
        migrations.AlterField(
            model_name="task",
            name="instructions",
            field=models.TextField(blank=True, verbose_name="instructions"),
        ),
        migrations.AlterField(
            model_name="task",
            name="name",
            field=models.CharField(max_length=64, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="task",
            name="stations",
            field=models.ManyToManyField(
                blank=True,
                related_name="tasks",
                to="iris.station",
                verbose_name="stations",
            ),
        ),
        migrations.AlterField(
            model_name="taskconsolidation",
            name="closing_tasks",
            field=models.ManyToManyField(
                related_name="consolidations",
                through="iris.TaskConsolidationClosingTasks",
                to="iris.task",
                verbose_name="closing tasks",
            ),
        ),
        migrations.AlterField(
            model_name="taskconsolidation",
            name="spawned_tasks",
            field=models.ManyToManyField(
                related_name="spawned_by_consolidation",
                through="iris.TaskConsolidationSpawnedTasks",
                to="iris.task",
                verbose_name="spawned tasks",
            ),
        ),
        migrations.AlterField(
            model_name="taskspawn",
            name="closing_task",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="spawns",
                to="iris.task",
                verbose_name="closing task",
            ),
        ),
        migrations.AlterField(
            model_name="taskspawn",
            name="spawned_tasks",
            field=models.ManyToManyField(
                related_name="spawned_by_tasks",
                through="iris.TaskSpawnSpawnedTasks",
                to="iris.task",
                verbose_name="spawned tasks",
            ),
        ),
        migrations.AlterField(
            model_name="work",
            name="cancel_reason",
            field=models.CharField(
                editable=False, max_length=256, verbose_name="cancelation reason"
            ),
        ),
        migrations.AlterField(
            model_name="work",
            name="cancel_time",
            field=models.DateTimeField(
                editable=False, null=True, verbose_name="cancelation time"
            ),
        ),
        migrations.AlterField(
            model_name="work",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="works",
                to="iris.category",
                verbose_name="category",
            ),
        ),
        migrations.AlterField(
            model_name="work",
            name="created",
            field=models.DateTimeField(auto_now_add=True, verbose_name="created"),
        ),
        migrations.AlterField(
            model_name="work",
            name="description",
            field=models.CharField(
                blank=True, max_length=128, verbose_name="description"
            ),
        ),
        migrations.AlterField(
            model_name="work",
            name="has_priority",
            field=models.BooleanField(default=False, verbose_name="has priority"),
        ),
        migrations.AlterField(
            model_name="work",
            name="modified",
            field=models.DateTimeField(auto_now=True, verbose_name="modified"),
        ),
        migrations.AlterField(
            model_name="work",
            name="notes",
            field=models.TextField(blank=True, verbose_name="notes"),
        ),
        migrations.AlterField(
            model_name="work",
            name="quantity",
            field=models.IntegerField(
                default=1,
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name="quantity",
            ),
        ),
        migrations.AlterField(
            model_name="worker",
            name="user",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
                verbose_name="user",
            ),
        ),
    ]
