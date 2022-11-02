from django.contrib.auth import get_user_model
from django.core.validators import ValidationError
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

NOTES_PATH_LIMIT = 64
NOTES_MAX_DISPLAY_LENGTH = 32


_notes_registry = set()


def get_note_types():
    return _notes_registry


def add_note_type(name, path):
    if len(path) > NOTES_PATH_LIMIT:
        raise RuntimeError(
            f"Notes registry path value must be under {NOTES_PATH_LIMIT} characters"
        )
    if (name, path) not in _notes_registry:
        _notes_registry.add((name, path))
    else:
        raise RuntimeError(f"Note types registry duplicate value for {name}, {path}")


class TimestampMixin(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CancelableMixin(models.Model):
    cancel_time = models.DateTimeField(editable=False, null=True)
    cancel_reason = models.CharField(max_length=256, editable=False)

    def cancel(reason):
        self.cancel_time = now()
        self.cancel_reason = reason
        self.save()

    @property
    def cancelled():
        return cancel_reason != "" or cancel_time is not None

    def clean(self):
        super().clean()
        if (self.cancel_reason != "" and self.cancel_time is None) or (
            self.cancel_reason == "" and self.cancel_time is not None
        ):
            raise ValidationError(
                _("Cancellation reason and time must be specified at the same time.")
            )

    class Meta:
        abstract = True


class NotesMixin(models.Model):
    notes = models.TextField(blank=True)

    class Meta:
        abstract = True


class Work(TimestampMixin, CancelableMixin, NotesMixin, models.Model):
    category = models.ForeignKey(
        "Category",
        on_delete=models.SET_NULL,
        related_name="works",
        null=True,
        blank=True,
    )

    def __str__(self):
        return str(_(f"Work {self.pk}"))


add_note_type("Work", "iris.app.Work")


class Category(models.Model):
    name = models.CharField(max_length=64)
    spawned_tasks = models.ManyToManyField(
        "Task",
        related_name="spawned_by_categories",
        through="CategorySpawnedTasks",
    )

    def __str__(self):
        return str(_(f"'{self.name}' category"))

    class Meta:
        verbose_name_plural = "categories"


class CategorySpawnedTasks(models.Model):
    category = models.ForeignKey("Category", on_delete=models.CASCADE)
    task = models.ForeignKey("Task", on_delete=models.RESTRICT)


class Task(models.Model):
    name = models.CharField(max_length=64)
    instructions = models.TextField(blank=True)
    stations = models.ManyToManyField("Station", related_name="tasks", blank=True)

    def __str__(self):
        return str(_(f"Task '{self.name}' ({self.pk})"))


class Job(TimestampMixin, models.Model):
    task = models.ForeignKey("Task", on_delete=models.RESTRICT, related_name="jobs")
    work = models.ForeignKey("Work", on_delete=models.RESTRICT, related_name="jobs")

    def __str__(self):
        return str(_(f"'{self.task.name}' for work {self.work.pk}"))


class TaskSpawn(models.Model):
    closing_task = models.ForeignKey(
        "Task", on_delete=models.CASCADE, related_name="spawns"
    )
    spawned_tasks = models.ManyToManyField(
        "Task",
        related_name="spawned_by_tasks",
        through="TaskSpawnSpawnedTasks",
    )

    def __str__(self):
        # (task, task, task)
        spawns_names = (
            "(" + ", ".join([f'"{task}"' for task in self.spawned_tasks.all()]) + ")"
        )
        return str(
            _(f'Spawns {spawns_names} when task "{self.closing_task}" is closed')
        )


class TaskSpawnSpawnedTasks(models.Model):
    task_spawn = models.ForeignKey("TaskSpawn", on_delete=models.CASCADE)
    task = models.ForeignKey("Task", on_delete=models.RESTRICT)


class TaskConsolidation(models.Model):
    closing_tasks = models.ManyToManyField(
        "Task", related_name="consolidations", through="TaskConsolidationClosingTasks"
    )
    spawned_tasks = models.ManyToManyField(
        "Task",
        related_name="spawned_by_consolidation",
        through="TaskConsolidationSpawnedTasks",
    )

    def __str__(self):
        # (task, task, task)
        spawns_names = (
            "(" + ", ".join([f'"{task}"' for task in self.spawned_tasks.all()]) + ")"
        )
        closing_names = (
            "(" + ", ".join([f'"{task}"' for task in self.closing_tasks.all()]) + ")"
        )
        return str(_(f"Spawns {spawns_names} when tasks {closing_names} are closed"))


class TaskConsolidationClosingTasks(models.Model):
    task_consolidation = models.ForeignKey(
        "TaskConsolidation", on_delete=models.CASCADE
    )
    task = models.ForeignKey("Task", on_delete=models.RESTRICT)


class TaskConsolidationSpawnedTasks(models.Model):
    task_consolidation = models.ForeignKey(
        "TaskConsolidation", on_delete=models.CASCADE
    )
    task = models.ForeignKey("Task", on_delete=models.RESTRICT)


class Worker(models.Model):
    user = models.OneToOneField(
        get_user_model(), on_delete=models.SET_NULL, null=True, blank=True
    )
    picture = models.ImageField(
        upload_to="worker_pictures/",
        height_field="picture_height",
        width_field="picture_width",
        null=True,
        blank=True,
    )
    picture_height = models.IntegerField(editable=False, null=True)
    picture_width = models.IntegerField(editable=False, null=True)

    def __str__(self):
        return str(self.user)


class Commit(TimestampMixin, NotesMixin, models.Model):
    job = models.OneToOneField("Job", on_delete=models.CASCADE)
    worker = models.OneToOneField("Worker", on_delete=models.RESTRICT)

    def __str__(self):
        return str(
            _(f'Commit for work "{self.job}" by worker {self.worker} ({self.modified})')
        )


add_note_type("Commit", "iris.app.Commit")


class Station(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class NoteTemplate(models.Model):
    path = models.CharField(max_length=NOTES_PATH_LIMIT)
    template = models.CharField(max_length=256)

    def __str__(self):
        # "Long string with many things" -> "Long stri..."
        short_template = (
            self.template
            if len(self.template) < NOTES_MAX_DISPLAY_LENGTH
            else self.template[: NOTES_MAX_DISPLAY_LENGTH - 3] + "..."
        )
        return str(_(f"{self.path} template: {short_template}"))


class Delay(TimestampMixin, NotesMixin, models.Model):
    job = models.ForeignKey("Job", on_delete=models.CASCADE, related_name="delays")
    worker = models.OneToOneField("Worker", on_delete=models.RESTRICT)
    time = models.DurationField()

    def __str__(self):
        return str(_(f'Delay "{self.job}" for {self.time}'))


add_note_type("Delay", "iris.app.Delay")


class Suspension(TimestampMixin, NotesMixin, models.Model):
    job = models.ForeignKey("Job", on_delete=models.CASCADE, related_name="suspensions")
    worker = models.OneToOneField("Worker", on_delete=models.RESTRICT)

    def __str__(self):
        return str(_(f'Suspension for "{self.job}"'))


add_note_type("Suspension", "iris.app.Suspension")


class Priority(TimestampMixin, NotesMixin, models.Model):
    job = models.ForeignKey("Job", on_delete=models.CASCADE, related_name="priorities")
    worker = models.OneToOneField("Worker", on_delete=models.RESTRICT)
    from_date = models.DateTimeField(default=now)
    score = models.IntegerField()

    def __str__(self):
        return str(_(f'Override "{self.job}" priority ({self.score})'))

    class Meta:
        verbose_name_plural = "priorities"


add_note_type("Priority", "iris.app.Priority")
