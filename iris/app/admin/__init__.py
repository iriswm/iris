from django.contrib import admin
from django.db.models import Count, F, Q
from django.urls import path
from django.utils.translation import gettext_lazy as _

from iris.app.admin.actions import (
    cancel_items,
    lift_suspensions,
    restore_items,
    spawn_and_consolidate_tasks,
    spawn_tasks,
)
from iris.app.admin.views import CancelItemsView
from iris.app.models import (
    Commit,
    Delay,
    Item,
    NoteTemplate,
    Process,
    ProcessSpawnedSteps,
    Station,
    Step,
    StepConsolidation,
    StepConsolidationClosingSteps,
    StepConsolidationSpawnedSteps,
    StepSpawn,
    StepSpawnSpawnedSteps,
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
    actions = [cancel_items, restore_items, spawn_tasks]
    list_display = ["__str__", "completed", "canceled"]
    list_filter = (ItemCompletionListFilter,)

    def get_urls(self):
        return [
            path(
                "cancel_items",
                self.admin_site.admin_view(CancelItemsView.as_view()),
                name="cancel_items",
            ),
            *super().get_urls(),
        ]


class ProcessSpawnedStepsInline(admin.TabularInline):
    model = ProcessSpawnedSteps


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    inlines = [ProcessSpawnedStepsInline]


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


class StepSpawnSpawnedStepsInline(admin.TabularInline):
    model = StepSpawnSpawnedSteps


@admin.register(StepSpawn)
class StepSpawnAdmin(admin.ModelAdmin):
    inlines = [StepSpawnSpawnedStepsInline]


class StepConsolidationClosingStepsInline(admin.TabularInline):
    model = StepConsolidationClosingSteps


class StepConsolidationSpawnedStepsInline(admin.TabularInline):
    model = StepConsolidationSpawnedSteps


@admin.register(StepConsolidation)
class StepConsolidationAdmin(admin.ModelAdmin):
    inlines = [StepConsolidationClosingStepsInline, StepConsolidationSpawnedStepsInline]


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    pass


@admin.register(Commit)
class CommitAdmin(admin.ModelAdmin):
    actions = [spawn_and_consolidate_tasks]


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
    actions = [lift_suspensions]
    list_display = ["__str__", "lifted"]

    @admin.display(description=_("Lifted"), boolean=True)
    def lifted(self, obj):
        return obj.lifted
