from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, ValidationError
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from iris.app.managers import DelayManager, ItemManager, SuspensionManager, TaskManager

NOTES_PATH_LIMIT = 64


class NotCanceledError(Exception):
    pass


class AlreadyCanceledError(Exception):
    pass


class NotSuspendedError(Exception):
    pass


class AlreadyEndedError(Exception):
    pass


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
        if self.canceled:
            raise AlreadyCanceledError(
                _("'{obj_name}' is already canceled.").format(
                    obj_name=str(self),
                ),
            )
        self.cancel_time = datetime_
        self.cancel_reason = reason
        self.save()

    def restore(self):
        if not self.canceled:
            raise NotCanceledError(
                _("'{obj_name}' is not canceled.").format(
                    obj_name=str(self),
                ),
            )
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


class Item(TimestampMixin, CancelableMixin, NotesMixin, models.Model):
    process = models.ForeignKey(
        "Process",
        verbose_name=_("process"),
        on_delete=models.RESTRICT,
        related_name="items",
    )
    description = models.CharField(_("description"), max_length=128, blank=True)
    quantity = models.IntegerField(
        _("quantity"), default=1, validators=[MinValueValidator(1)]
    )
    has_priority = models.BooleanField(_("has priority"), default=False)

    objects = ItemManager()

    class Meta:
        verbose_name = _("item")
        verbose_name_plural = _("items")

    @property
    def completed(self):
        all_tasks = Task.objects.filter(item=self)
        return all([task.completed for task in all_tasks])

    def spawn_tasks(self):
        for transition in self.process.step_transitions.all():
            if transition.required_steps.count() == 0:
                new_task = Task(item=self, step_transition=transition)
                new_task.save()


add_note_type("Item", "iris.app.Item")


class Process(models.Model):
    name = models.CharField(_("name"), max_length=64)

    class Meta:
        verbose_name = _("process")
        verbose_name_plural = _("processes")


class Step(models.Model):
    name = models.CharField(_("name"), max_length=64)
    instructions = models.TextField(_("instructions"), blank=True)
    stations = models.ManyToManyField(
        "Station", verbose_name=_("stations"), related_name="steps", blank=True
    )

    class Meta:
        verbose_name = _("step")
        verbose_name_plural = _("steps")


class Task(TimestampMixin, models.Model):
    step_transition = models.ForeignKey(
        "StepTransition",
        verbose_name=_("step transition"),
        on_delete=models.RESTRICT,
        related_name="tasks",
    )
    item = models.ForeignKey(
        "Item", verbose_name=_("item"), on_delete=models.RESTRICT, related_name="tasks"
    )

    objects = TaskManager()

    class Meta:
        verbose_name = _("task")
        verbose_name_plural = _("tasks")

    @property
    def canceled(self):
        return self.item.canceled

    @property
    def completed(self):
        return hasattr(self, "commit")

    @property
    def delayed(self):
        return any(
            [(delay.created + delay.duration) > now() for delay in self.delays.all()]
        )

    @property
    def delayed_by(self):
        for delay in self.delays.all():
            if (delay.created + delay.duration) > now():
                return delay

    @property
    def suspended(self):
        return any([not suspension.lifted for suspension in self.suspensions.all()])

    @property
    def suspended_by(self):
        for suspension in self.suspensions.all():
            if not suspension.lifted:
                return suspension


class StepTransition(models.Model):
    process = models.ForeignKey(
        "Process",
        verbose_name=_("process"),
        on_delete=models.CASCADE,
        related_name="step_transitions",
    )
    required_steps = models.ManyToManyField(
        "self",
        verbose_name=_("required steps"),
        through="StepTransitionRequiredSteps",
        symmetrical=False,
        related_name="required_by",
    )
    creates = models.ForeignKey(
        "Step",
        verbose_name=_("creates"),
        on_delete=models.RESTRICT,
        related_name="created_by",
    )

    class Meta:
        verbose_name = _("step transition")
        verbose_name_plural = _("step transitions")


class StepTransitionRequiredSteps(models.Model):
    step_transition = models.ForeignKey(
        "StepTransition", on_delete=models.CASCADE, related_name="step_transition"
    )
    requirement = models.ForeignKey(
        "StepTransition", on_delete=models.CASCADE, related_name="requirement"
    )


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


class Commit(TimestampMixin, NotesMixin, models.Model):
    task = models.OneToOneField(
        "Task", verbose_name=_("task"), on_delete=models.CASCADE
    )
    worker = models.ForeignKey(
        "Worker",
        verbose_name=_("worker"),
        on_delete=models.RESTRICT,
        related_name="commits",
    )

    class Meta:
        verbose_name = _("commit")
        verbose_name_plural = _("commits")

    def spawn_and_consolidate_tasks(self):
        for required_by in self.task.step_transition.required_by.all():
            required_steps = required_by.required_steps.all()
            required_tasks = Task.objects.filter(
                item=self.task.item, step_transition__in=required_steps
            )
            if len(required_steps) == len(required_tasks) and all(
                [task.completed for task in required_tasks]
            ):
                new_task = Task(item=self.task.item, step_transition=required_by)
                new_task.save()


add_note_type("Commit", "iris.app.Commit")


class Station(models.Model):
    name = models.CharField(_("name"), max_length=64)

    class Meta:
        verbose_name = _("station")
        verbose_name_plural = _("stations")


class NoteTemplate(models.Model):
    path = models.CharField(_("path"), max_length=NOTES_PATH_LIMIT)
    template = models.CharField(_("template"), max_length=256)

    class Meta:
        verbose_name = _("note template")
        verbose_name_plural = _("note templates")


class Delay(TimestampMixin, NotesMixin, models.Model):
    task = models.ForeignKey(
        "Task", verbose_name=_("task"), on_delete=models.CASCADE, related_name="delays"
    )
    worker = models.ForeignKey(
        "Worker",
        verbose_name=_("worker"),
        on_delete=models.RESTRICT,
        related_name="delays",
    )
    duration = models.DurationField(_("duration"))

    objects = DelayManager()

    class Meta:
        verbose_name = _("delay")
        verbose_name_plural = _("delays")

    @property
    def in_effect(self):
        return self.created + self.duration > now()

    @property
    def ends(self):
        return self.created + self.duration

    def end(self):
        if not self.in_effect:
            raise AlreadyEndedError(
                _("Delay '{delay_name}' has already ended.").format(
                    delay_name=str(self),
                )
            )
        self.duration = now() - self.created
        self.save()


add_note_type("Delay", "iris.app.Delay")


class Suspension(TimestampMixin, NotesMixin, models.Model):
    task = models.ForeignKey(
        "Task",
        verbose_name=_("task"),
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

    objects = SuspensionManager()

    class Meta:
        verbose_name = _("suspension")
        verbose_name_plural = _("suspensions")

    def lift(self, datetime_=None):
        if self.lifted:
            raise NotSuspendedError(
                _("Suspension '{suspension_name}' is already lifted.").format(
                    suspension_name=str(self),
                )
            )
        if datetime_ is None:
            datetime_ = now()
        self.lifted_at = datetime_
        self.save()

    @property
    def lifted(self):
        return self.lifted_at is not None


add_note_type("Suspension", "iris.app.Suspension")
