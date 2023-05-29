from django.contrib import admin
from django.db.models import Count, F, Q
from django.forms import ModelChoiceField, ModelMultipleChoiceField
from django.urls import path, resolve
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _

from iris.app.admin.actions import (
    commits_spawn_tasks,
    delays_end_now,
    items_cancel,
    items_restore,
    items_spawn_tasks,
    suspensions_lift,
)
from iris.app.admin.views import (
    CommitSpawnAndConsolidateTasksView,
    ItemCancelView,
    ItemSpawnTasksView,
)
from iris.app.models import (
    Commit,
    Delay,
    Item,
    NoteTemplate,
    Process,
    Station,
    Step,
    StepTransition,
    StepTransitionRequiredSteps,
    Suspension,
    Task,
    Worker,
)


class CompletableAdminMixin:
    @admin.display(description=_("Completed"), boolean=True)
    def completed(self, obj):
        return obj.completed


class CancelableAdminMixin:
    @admin.display(description=_("Canceled"), boolean=True)
    def canceled(self, obj):
        return obj.canceled


class ItemCompletionListFilter(admin.SimpleListFilter):
    title = _("completion status")
    parameter_name = "completion"

    def lookups(self, request, model_admin):
        return (
            ("completed", _("Completed")),
            ("notcompleted", _("Not completed")),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        queryset = queryset.annotate(
            total_tasks=Count("tasks"),
            completed_tasks=Count("tasks", filter=Q(tasks__commit__isnull=False)),
        )
        if self.value() == "completed":
            return queryset.filter(total_tasks=F("completed_tasks"))
        else:
            return queryset.exclude(total_tasks=F("completed_tasks"))


class ProcessModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


@admin.register(Item)
class ItemAdmin(CompletableAdminMixin, CancelableAdminMixin, admin.ModelAdmin):
    actions = [items_cancel, items_restore, items_spawn_tasks]
    list_display = ["id", "item_description", "process_name", "completed", "canceled"]
    list_display_links = ["id", "item_description"]
    list_filter = (ItemCompletionListFilter,)

    @admin.display(description=_("Description"))
    def item_description(self, obj):
        return (
            "---"
            if obj.description == ""
            else f"{Truncator(obj.description).chars(32)}"
        )

    @admin.display(description=_("Process"))
    def process_name(self, obj):
        return obj.process.name

    def get_urls(self):
        return [
            path(
                "iris_item_cancel",
                self.admin_site.admin_view(ItemCancelView.as_view()),
                name="iris_item_cancel",
            ),
            path(
                "iris_item_spawn_tasks",
                self.admin_site.admin_view(ItemSpawnTasksView.as_view()),
                name="iris_item_spawn_tasks",
            ),
            *super().get_urls(),
        ]

    def get_exclude(self, request, obj=None):
        item_exists_and_has_tasks = (
            obj is not None and Task.objects.filter(item=obj).count() > 0
        )
        return ["process"] if item_exists_and_has_tasks else []

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "process":
            kwargs["form_class"] = ProcessModelChoiceField
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    list_display_links = ["id", "name"]


class StationModelMultipleChoiceField(ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name


@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "assigned_stations"]
    list_display_links = ["id", "name"]

    def assigned_stations(self, obj):
        return ", ".join(station.name for station in obj.stations.all())

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "stations":
            kwargs["form_class"] = StationModelMultipleChoiceField
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class TaskCompletionListFilter(admin.SimpleListFilter):
    title = _("completion status")
    parameter_name = "completion"

    def lookups(self, request, model_admin):
        return (
            ("completed", _("Completed")),
            ("notcompleted", _("Not completed")),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        if self.value() == "completed":
            return queryset.filter(commit__isnull=False)
        else:
            return queryset.filter(commit__isnull=True)


@admin.register(Task)
class TaskAdmin(CompletableAdminMixin, admin.ModelAdmin):
    list_display = ["id", "task_description", "item_name", "completed"]
    list_display_links = None
    list_filter = (TaskCompletionListFilter,)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request):
        return False

    @admin.display(description=_("Description"))
    def task_description(self, obj):
        return _("Task for step '{obj.step_transition.creates.name}'").format(obj=obj)

    @admin.display(description=_("Item"))
    def item_name(self, obj):
        quantity_suffix = "" if obj.item.quantity == 1 else f" x{obj.item.quantity}"
        return (
            f"#{obj.item.pk}{quantity_suffix}"
            if obj.item.description == ""
            else f"#{obj.item.pk} ({Truncator(obj.item.description).chars(16)}){quantity_suffix}"
        )


def format_transition(obj):
    if obj.required_steps.count() == 0:
        return _(
            "Spawns a task for step '{obj.creates.name}' when the process '{obj.process.name}' starts"
        ).format(
            obj=obj,
        )
    else:
        # (step, step, step)
        required_names = (
            "("
            + ", ".join(
                [
                    f"'{transition.creates.name}'"
                    for transition in obj.required_steps.all()
                ]
            )
            + ")"
        )
        return _(
            "Spawns a task for step '{obj.creates.name}' when steps {required_names} are closed"
        ).format(
            obj=obj,
            required_names=required_names,
        )


class StepTransitionModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return format_transition(obj)


class StepTransitionRequiredStepsInline(admin.TabularInline):
    model = StepTransitionRequiredSteps
    fk_name = "step_transition"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "requirement":
            path_kwargs = resolve(request.path).kwargs
            if "object_id" in path_kwargs:
                parent_id = int(path_kwargs["object_id"])
                parent_process = self.parent_model.objects.get(pk=parent_id).process
                kwargs["queryset"] = StepTransition.objects.filter(
                    process=parent_process
                )
                kwargs["form_class"] = StepTransitionModelChoiceField
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class StepModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return _("Step '{obj.name}'").format(obj=obj)


@admin.register(StepTransition)
class StepTransitionAdmin(admin.ModelAdmin):
    list_display = ["id", "transition_description", "process_name"]
    list_display_links = ["id", "transition_description"]
    inlines = [StepTransitionRequiredStepsInline]

    @admin.display(description=_("Description"))
    def transition_description(self, obj):
        return format_transition(obj)

    @admin.display(description=_("Process"))
    def process_name(self, obj):
        return obj.process.name

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "process":
            kwargs["form_class"] = ProcessModelChoiceField
        if db_field.name == "creates":
            kwargs["form_class"] = StepModelChoiceField
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ["id", "assigned_user"]
    list_display_links = ["id", "assigned_user"]

    @admin.display(description=_("Assigned user"))
    def assigned_user(self, obj):
        return _("Profile assigned to user '{obj.user.username}'").format(obj=obj)


def format_item_for_status(obj):
    return (
        f"#{obj.pk} ---"
        if obj.description == ""
        else f"#{obj.pk} ({Truncator(obj.description).chars(16)})"
    )


@admin.register(Commit)
class CommitAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "step_description",
        "stations",
        "item_description",
        "worker_name",
        "date_modified",
        "transition_description",
    ]
    list_display_links = None
    actions = [commits_spawn_tasks]

    def has_add_permission(self, request):
        return False

    @admin.display(description=_("Step"))
    def step_description(self, obj):
        return obj.task.step_transition.creates.name

    @admin.display(description=_("Stations"))
    def stations(self, obj):
        stations = obj.task.step_transition.creates.stations
        return ", ".join(station.name for station in stations.all())

    @admin.display(description=_("Item"))
    def item_description(self, obj):
        return format_item_for_status(obj.task.item)

    @admin.display(description=_("Worker"))
    def worker_name(self, obj):
        return obj.worker.user.username

    @admin.display(description=_("Modified"))
    def date_modified(self, obj):
        return obj.modified

    @admin.display(description=_("Transition"))
    def transition_description(self, obj):
        return format_transition(obj.task.step_transition)

    def get_urls(self):
        return [
            path(
                "iris_commit_spawn_tasks",
                self.admin_site.admin_view(
                    CommitSpawnAndConsolidateTasksView.as_view()
                ),
                name="iris_commit_spawn_tasks",
            ),
            *super().get_urls(),
        ]


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    list_display_links = ["id", "name"]


@admin.register(NoteTemplate)
class NoteTemplateAdmin(admin.ModelAdmin):
    list_display = ["id", "path", "template_contents"]
    list_display_links = ["id", "path", "template_contents"]

    @admin.display(description=_("Template contents"))
    def template_contents(self, obj):
        return Truncator(obj.template).chars(128)


@admin.register(Delay)
class DelayAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "duration",
        "step_description",
        "stations",
        "item_description",
        "worker_name",
        "date_created",
        "date_until",
        "transition_description",
    ]
    list_display_links = ["id", "duration"]
    fields = ["notes", "duration"]
    actions = [delays_end_now]

    def has_add_permission(self, request):
        return False

    @admin.display(description=_("Step"))
    def step_description(self, obj):
        return obj.task.step_transition.creates.name

    @admin.display(description=_("Stations"))
    def stations(self, obj):
        stations = obj.task.step_transition.creates.stations
        return ", ".join(station.name for station in stations.all())

    @admin.display(description=_("Item"))
    def item_description(self, obj):
        return format_item_for_status(obj.task.item)

    @admin.display(description=_("Worker"))
    def worker_name(self, obj):
        return obj.worker.user.username

    @admin.display(description=_("Created"))
    def date_created(self, obj):
        return obj.modified

    @admin.display(description=_("Ends"))
    def date_until(self, obj):
        return obj.ends

    @admin.display(description=_("Transition"))
    def transition_description(self, obj):
        return format_transition(obj.task.step_transition)


@admin.register(Suspension)
class SuspensionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "lifted",
        "step_description",
        "stations",
        "item_description",
        "worker_name",
        "date_created",
        "transition_description",
    ]
    list_display_links = ["id", "lifted"]
    actions = [suspensions_lift]
    fields = ["notes"]

    def has_add_permission(self, request):
        return False

    @admin.display(description=_("Step"))
    def step_description(self, obj):
        return obj.task.step_transition.creates.name

    @admin.display(description=_("Stations"))
    def stations(self, obj):
        stations = obj.task.step_transition.creates.stations
        return ", ".join(station.name for station in stations.all())

    @admin.display(description=_("Item"))
    def item_description(self, obj):
        return format_item_for_status(obj.task.item)

    @admin.display(description=_("Worker"))
    def worker_name(self, obj):
        return obj.worker.user.username

    @admin.display(description=_("Created"))
    def date_created(self, obj):
        return obj.modified

    @admin.display(description=_("Transition"))
    def transition_description(self, obj):
        return format_transition(obj.task.step_transition)

    @admin.display(description=_("Lifted"), boolean=True)
    def lifted(self, obj):
        return obj.lifted
