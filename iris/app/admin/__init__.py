from django.contrib import admin
from django.db.models import Count, F, Q
from django.urls import path, resolve
from django.utils.translation import gettext_lazy as _

from iris.app.admin.actions import (
    commits_spawn_tasks,
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


@admin.register(Item)
class ItemAdmin(CompletableAdminMixin, CancelableAdminMixin, admin.ModelAdmin):
    actions = [items_cancel, items_restore, items_spawn_tasks]
    list_display = ["__str__", "process", "completed", "canceled"]
    list_filter = (ItemCompletionListFilter,)

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


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    pass


@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    pass


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
    list_display = ["__str__", "completed"]
    list_filter = (TaskCompletionListFilter,)


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
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(StepTransition)
class StepTransitionAdmin(admin.ModelAdmin):
    inlines = [StepTransitionRequiredStepsInline]


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    pass


@admin.register(Commit)
class CommitAdmin(admin.ModelAdmin):
    actions = [commits_spawn_tasks]

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
    pass


@admin.register(NoteTemplate)
class NoteTemplateAdmin(admin.ModelAdmin):
    pass


@admin.register(Delay)
class DelayAdmin(admin.ModelAdmin):
    pass


@admin.register(Suspension)
class SuspensionAdmin(admin.ModelAdmin):
    actions = [suspensions_lift]
    list_display = ["__str__", "lifted"]

    @admin.display(description=_("Lifted"), boolean=True)
    def lifted(self, obj):
        return obj.lifted
