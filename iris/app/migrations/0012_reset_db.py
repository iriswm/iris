# Generated by Django 4.1.1 on 2023-02-07 19:05

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("iris", "0011_initial"),
    ]
    operations = [
        migrations.DeleteModel(
            name="Commit",
        ),
        migrations.DeleteModel(
            name="Delay",
        ),
        migrations.DeleteModel(
            name="Item",
        ),
        migrations.DeleteModel(
            name="NoteTemplate",
        ),
        migrations.DeleteModel(
            name="Process",
        ),
        migrations.DeleteModel(
            name="ProcessSpawnedSteps",
        ),
        migrations.DeleteModel(
            name="Station",
        ),
        migrations.DeleteModel(
            name="Step",
        ),
        migrations.DeleteModel(
            name="StepConsolidation",
        ),
        migrations.DeleteModel(
            name="StepConsolidationClosingSteps",
        ),
        migrations.DeleteModel(
            name="StepConsolidationSpawnedSteps",
        ),
        migrations.DeleteModel(
            name="StepSpawn",
        ),
        migrations.DeleteModel(
            name="StepSpawnSpawnedSteps",
        ),
        migrations.DeleteModel(
            name="Suspension",
        ),
        migrations.DeleteModel(
            name="Task",
        ),
        migrations.DeleteModel(
            name="Worker",
        ),
    ]