from django.contrib.auth import get_user_model
from django.core.validators import ValidationError
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


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


class Order(TimestampMixin, CancelableMixin, NotesMixin):
    wc_order_id = models.IntegerField(_("WooCommerce order ID"))
    wc_order_notes = models.TextField(_("WooCommerce order notes"), blank=True)

    def cancel(reason):
        super().cancel(reason)
        for line in self.lines.all():
            line.cancel(reason)

    def __str__(self):
        return str(_(f"WooCommerce order {self.wc_order_id}"))


class WooCommerceCategoryMixin(models.Model):
    wc_category_id = models.IntegerField(_("WooCommerce category ID"))

    class Meta:
        abstract = True


class Line(TimestampMixin, CancelableMixin, NotesMixin, WooCommerceCategoryMixin):
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="lines")
    wc_order_item_id = models.IntegerField(_("WooCommerce order line ID"))

    def __str__(self):
        return str(
            _(
                f"WooCommerce line {self.wc_order_item_id} for order {self.order.wc_order_id}"
            )
        )


class Category(WooCommerceCategoryMixin):
    name = models.CharField(max_length=64)
    spawned_tasks = models.ManyToManyField(
        "Task", related_name="spawned_by_categories", blank=True
    )

    def __str__(self):
        return f"{self.name} ({self.pk})"

    class Meta:
        verbose_name_plural = "categories"


class Task(models.Model):
    name = models.CharField(max_length=64)
    instructions = models.TextField(blank=True)
    average_hours = models.IntegerField(null=True, blank=True)
    stations = models.ManyToManyField("Station", related_name="tasks", blank=True)

    def __str__(self):
        return f"{self.name} ({self.pk})"


class Work(TimestampMixin):
    task = models.ForeignKey("Task", on_delete=models.RESTRICT, related_name="works")
    line = models.ForeignKey("Line", on_delete=models.CASCADE, related_name="works")

    def __str__(self):
        return str(
            _(
                f"'{self.task.name}' for order id {self.line.order.pk}, line id {self.line.pk}"
            )
        )


class TaskSpawn(models.Model):
    closing_task = models.ForeignKey(
        "Task", on_delete=models.CASCADE, related_name="spawns"
    )
    spawned_tasks = models.ManyToManyField("Task", related_name="spawned_by_tasks")

    def __str__(self):
        # (task, task, task)
        spawns_names = (
            "(" + ", ".join([f"'{task}'" for task in self.spawned_tasks.all()]) + ")"
        )
        return str(
            _(f'Spawns {spawns_names} when task "{self.closing_task}" is closed')
        )


class TaskConsolidation(models.Model):
    closing_tasks = models.ManyToManyField("Task", related_name="consolidations")
    spawned_tasks = models.ManyToManyField(
        "Task", related_name="spawned_by_consolidation"
    )

    def __str__(self):
        # (task, task, task)
        spawns_names = (
            "(" + ", ".join([f"'{task}'" for task in self.spawned_tasks.all()]) + ")"
        )
        closing_names = (
            "(" + ", ".join([f"'{task}'" for task in self.closing_tasks.all()]) + ")"
        )
        return str(_(f"Spawns {spawns_names} when tasks {closing_names} are closed"))


class Worker(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.RESTRICT)
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


class Commit(TimestampMixin, NotesMixin):
    work = models.OneToOneField("Work", on_delete=models.RESTRICT)
    worker = models.OneToOneField("Worker", on_delete=models.RESTRICT)

    def __str__(self):
        return str(
            _(
                f'Commit for work "{self.work}" by worker {self.worker} ({self.modified})'
            )
        )


class Station(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class NoteTemplate(models.Model):
    KIND_SHORT_LIMIT = 32

    ORDER, LINE, COMMIT, DELAY, SUSPENSION, PRIORITY = range(6)
    KIND_CHOICES = [
        (ORDER, "Order"),
        (LINE, "Line"),
        (COMMIT, "Commit"),
        (DELAY, "Delay"),
        (SUSPENSION, "Suspension"),
        (PRIORITY, "Priority"),
    ]

    kind = models.IntegerField(default=COMMIT, choices=KIND_CHOICES)
    template = models.CharField(max_length=256)

    def __str__(self):
        # "Long string with many things" -> "Long stri..."
        template_name = self.KIND_CHOICES[self.kind][1]
        short_template = (
            self.template
            if len(self.template) < self.KIND_SHORT_LIMIT
            else self.template[:28] + "..."
        )
        return str(_(f"{template_name} template: {short_template}"))


class Delay(TimestampMixin, NotesMixin):
    work = models.ForeignKey("Work", on_delete=models.CASCADE, related_name="delays")
    worker = models.OneToOneField("Worker", on_delete=models.RESTRICT)
    time = models.DurationField()

    def __str__(self):
        return str(_(f'Delay "{self.work}" for {self.time}'))


class Suspension(TimestampMixin, NotesMixin):
    work = models.ForeignKey(
        "Work", on_delete=models.CASCADE, related_name="suspensions"
    )
    worker = models.OneToOneField("Worker", on_delete=models.RESTRICT)

    def __str__(self):
        return str(_(f'Suspension for "{self.work}"'))


class Priority(TimestampMixin, NotesMixin):
    work = models.ForeignKey(
        "Work", on_delete=models.CASCADE, related_name="priorities"
    )
    worker = models.OneToOneField("Worker", on_delete=models.RESTRICT)
    from_date = models.DateTimeField(default=now)
    score = models.IntegerField()

    def __str__(self):
        return str(_(f'Override "{self.work}" priority ({self.score})'))

    class Meta:
        verbose_name_plural = "priorities"
