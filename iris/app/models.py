from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, ValidationError
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
    created = models.DateTimeField(_("created"), auto_now_add=True)
    modified = models.DateTimeField(_("modified"), auto_now=True)

    class Meta:
        abstract = True


class CancelableMixin(models.Model):
    cancel_time = models.DateTimeField(_("cancelation time"), editable=False, null=True)
    cancel_reason = models.CharField(
        _("cancelation reason"), max_length=256, editable=False
    )

    class Meta:
        abstract = True

    def cancel(self, reason, datetime_=None):
        if datetime_ is None:
            datetime_ = now()
        self.cancel_time = datetime_
        self.cancel_reason = reason
        self.save()

    def restore(self):
        self.cancel_time = None
        self.cancel_reason = ""
        self.save()

    @property
    def canceled(self):
        return self.cancel_reason != "" or self.cancel_time is not None

    def clean(self):
        super().clean()
        if (self.cancel_reason != "" and self.cancel_time is None) or (
            self.cancel_reason == "" and self.cancel_time is not None
        ):
            raise ValidationError(
                _("Cancelation reason and time must be specified at the same time.")
            )


class NotesMixin(models.Model):
    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        abstract = True


class Work(TimestampMixin, CancelableMixin, NotesMixin, models.Model):
    category = models.ForeignKey(
        "Category",
        verbose_name=_("category"),
        on_delete=models.SET_NULL,
        related_name="works",
        null=True,
        blank=True,
    )
    description = models.CharField(_("description"), max_length=128, blank=True)
    quantity = models.IntegerField(
        _("quantity"), default=1, validators=[MinValueValidator(1)]
    )
    has_priority = models.BooleanField(_("has priority"), default=False)

    class Meta:
        verbose_name = _("work")
        verbose_name_plural = _("works")

    def __str__(self):
        str_ = _("Work {obj.pk}").format(obj=self)
        if self.description != "":
            str_ = f"{str_}: {self.description}"
        return str_

    @property
    def completed(self):
        all_jobs = Job.objects.filter(work=self)
        return all([job.completed for job in all_jobs])

    def spawn_jobs(self):
        if self.category is None:
            return
        for task in self.category.spawned_tasks.all():
            new_job = Job(work=self, task=task)
            new_job.save()


add_note_type("Work", "iris.app.Work")


class Category(models.Model):
    name = models.CharField(_("name"), max_length=64)
    spawned_tasks = models.ManyToManyField(
        "Task",
        verbose_name=_("spawned tasks"),
        related_name="spawned_by_categories",
        through="CategorySpawnedTasks",
    )

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    def __str__(self):
        return _("'{obj.name}' category").format(obj=self)


class CategorySpawnedTasks(models.Model):
    category = models.ForeignKey("Category", on_delete=models.CASCADE)
    task = models.ForeignKey("Task", on_delete=models.RESTRICT)


class Task(models.Model):
    name = models.CharField(_("name"), max_length=64)
    instructions = models.TextField(_("instructions"), blank=True)
    stations = models.ManyToManyField(
        "Station", verbose_name=_("stations"), related_name="tasks", blank=True
    )

    class Meta:
        verbose_name = _("task")
        verbose_name_plural = _("tasks")

    def __str__(self):
        return _("Task '{obj.name}' ({obj.pk})").format(obj=self)


class Job(TimestampMixin, models.Model):
    task = models.ForeignKey(
        "Task", verbose_name=_("task"), on_delete=models.RESTRICT, related_name="jobs"
    )
    work = models.ForeignKey(
        "Work", verbose_name=_("work"), on_delete=models.RESTRICT, related_name="jobs"
    )

    class Meta:
        verbose_name = _("job")
        verbose_name_plural = _("jobs")

    def __str__(self):
        quantity_suffix = "" if self.work.quantity == 1 else f" x{self.work.quantity}"
        return _("'{obj.task.name}' for work {obj.work.pk}{quantity_suffix}").format(
            obj=self,
            quantity_suffix=quantity_suffix,
        )

    @property
    def completed(self):
        return Commit.objects.filter(job=self).exists()


class TaskSpawn(models.Model):
    closing_task = models.ForeignKey(
        "Task",
        verbose_name=_("closing task"),
        on_delete=models.CASCADE,
        related_name="spawns",
    )
    spawned_tasks = models.ManyToManyField(
        "Task",
        verbose_name=_("spawned tasks"),
        related_name="spawned_by_tasks",
        through="TaskSpawnSpawnedTasks",
    )

    class Meta:
        verbose_name = _("task spawn")
        verbose_name_plural = _("task spawns")

    def __str__(self):
        # (task, task, task)
        spawns_names = (
            "(" + ", ".join([f'"{task}"' for task in self.spawned_tasks.all()]) + ")"
        )
        return _(
            'Spawns {spawns_names} when task "{obj.closing_task}" is closed'
        ).format(
            obj=self,
            spawns_names=spawns_names,
        )


class TaskSpawnSpawnedTasks(models.Model):
    task_spawn = models.ForeignKey("TaskSpawn", on_delete=models.CASCADE)
    task = models.ForeignKey("Task", on_delete=models.RESTRICT)


class TaskConsolidation(models.Model):
    closing_tasks = models.ManyToManyField(
        "Task",
        verbose_name=_("closing tasks"),
        related_name="consolidations",
        through="TaskConsolidationClosingTasks",
    )
    spawned_tasks = models.ManyToManyField(
        "Task",
        verbose_name=_("spawned tasks"),
        related_name="spawned_by_consolidation",
        through="TaskConsolidationSpawnedTasks",
    )

    class Meta:
        verbose_name = _("task consolidation")
        verbose_name_plural = _("task consolidations")

    def __str__(self):
        # (task, task, task)
        spawns_names = (
            "(" + ", ".join([f'"{task}"' for task in self.spawned_tasks.all()]) + ")"
        )
        closing_names = (
            "(" + ", ".join([f'"{task}"' for task in self.closing_tasks.all()]) + ")"
        )
        return _("Spawns {spawns_names} when tasks {closing_names} are closed").format(
            spawns_names=spawns_names,
            closing_names=closing_names,
        )


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
        get_user_model(),
        verbose_name=_("user"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("worker")
        verbose_name_plural = _("workers")

    def __str__(self):
        return str(self.user)


class Commit(TimestampMixin, NotesMixin, models.Model):
    job = models.OneToOneField("Job", verbose_name=_("job"), on_delete=models.CASCADE)
    worker = models.ForeignKey(
        "Worker",
        verbose_name=_("worker"),
        on_delete=models.RESTRICT,
        related_name="commits",
    )

    class Meta:
        verbose_name = _("commit")
        verbose_name_plural = _("commits")

    def __str__(self):
        return _(
            'Commit for work "{obj.job}" by worker {obj.worker} ({obj.modified})'
        ).format(
            obj=self,
        )

    def spawn_and_consolidate_jobs(self):
        for spawn in self.job.task.spawns.all():
            for task in spawn.spawned_tasks.all():
                new_job = Job(work=self.job.work, task=task)
                new_job.save()
        for consolidation in self.job.task.consolidations.all():
            closing_jobs = Job.objects.filter(
                work=self.job.work, task__in=consolidation.closing_tasks.all()
            )
            if all([job.completed for job in closing_jobs]):
                for task in consolidation.spawned_tasks.all():
                    new_job = Job(work=self.job.work, task=task)
                    new_job.save()


add_note_type("Commit", "iris.app.Commit")


class Station(models.Model):
    name = models.CharField(_("name"), max_length=64)

    class Meta:
        verbose_name = _("station")
        verbose_name_plural = _("stations")

    def __str__(self):
        return self.name


class NoteTemplate(models.Model):
    path = models.CharField(_("path"), max_length=NOTES_PATH_LIMIT)
    template = models.CharField(_("template"), max_length=256)

    class Meta:
        verbose_name = _("note template")
        verbose_name_plural = _("note templates")

    def __str__(self):
        # "Long string with many things" -> "Long stri..."
        short_template = (
            self.template
            if len(self.template) < NOTES_MAX_DISPLAY_LENGTH
            else self.template[: NOTES_MAX_DISPLAY_LENGTH - 3] + "..."
        )
        return _("{obj.path} template: {short_template}").format(
            obj=self,
            short_template=short_template,
        )


class Delay(TimestampMixin, NotesMixin, models.Model):
    job = models.ForeignKey(
        "Job", verbose_name=_("job"), on_delete=models.CASCADE, related_name="delays"
    )
    worker = models.ForeignKey(
        "Worker",
        verbose_name=_("worker"),
        on_delete=models.RESTRICT,
        related_name="delays",
    )
    duration = models.DurationField(_("duration"))

    class Meta:
        verbose_name = _("delay")
        verbose_name_plural = _("delays")

    def __str__(self):
        return _('Delay "{obj.job}" for {obj.duration}').format(obj=self)


add_note_type("Delay", "iris.app.Delay")


class Suspension(TimestampMixin, NotesMixin, models.Model):
    job = models.ForeignKey(
        "Job",
        verbose_name=_("job"),
        on_delete=models.CASCADE,
        related_name="suspensions",
    )
    worker = models.ForeignKey(
        "Worker",
        verbose_name=_("worker"),
        on_delete=models.RESTRICT,
        related_name="suspensions",
    )
    lifted_at = models.DateTimeField(
        _("lifted_at"),
        editable=False,
        null=True,
    )

    class Meta:
        verbose_name = _("suspension")
        verbose_name_plural = _("suspensions")

    def lift(self, datetime_=None):
        if datetime_ is None:
            datetime_ = now()
        self.lifted_at = datetime_
        self.save()

    @property
    def lifted(self):
        return self.lifted_at < now()

    def __str__(self):
        return _('Suspension for "{obj.job}"').format(obj=self)


add_note_type("Suspension", "iris.app.Suspension")
