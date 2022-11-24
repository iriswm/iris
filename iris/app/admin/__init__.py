from django.contrib import admin
from django.db.models import Count, F, Q
from django.urls import path
from django.utils.translation import gettext_lazy as _

from iris.app.admin.actions import (
    cancel_works,
    lift_suspensions,
    restore_works,
    spawn_and_consolidate_jobs,
    spawn_jobs,
)
from iris.app.admin.views import CancelWorksView
from iris.app.models import (
    Category,
    CategorySpawnedTasks,
    Commit,
    Delay,
    Job,
    NoteTemplate,
    Station,
    Suspension,
    Task,
    TaskConsolidation,
    TaskConsolidationClosingTasks,
    TaskConsolidationSpawnedTasks,
    TaskSpawn,
    TaskSpawnSpawnedTasks,
    Work,
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


class WorkCompletionListFilter(admin.SimpleListFilter):
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
            total_jobs=Count("jobs"),
            completed_jobs=Count("jobs", filter=Q(jobs__commit__isnull=False)),
        )
        if self.value() == "completed":
            return queryset.filter(total_jobs=F("completed_jobs"))
        else:
            return queryset.exclude(total_jobs=F("completed_jobs"))


@admin.register(Work)
class WorkAdmin(CompletableAdminMixin, CancelableAdminMixin, admin.ModelAdmin):
    actions = [cancel_works, restore_works, spawn_jobs]
    list_display = ["__str__", "completed", "canceled"]
    list_filter = (WorkCompletionListFilter,)

    def get_urls(self):
        return [
            path(
                "cancel_works",
                self.admin_site.admin_view(CancelWorksView.as_view()),
                name="cancel_works",
            ),
            *super().get_urls(),
        ]


class CategorySpawnedTasksInline(admin.TabularInline):
    model = CategorySpawnedTasks


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = [CategorySpawnedTasksInline]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    pass


class JobCompletionListFilter(admin.SimpleListFilter):
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


@admin.register(Job)
class JobAdmin(CompletableAdminMixin, admin.ModelAdmin):
    list_display = ["__str__", "completed"]
    list_filter = (JobCompletionListFilter,)


class TaskSpawnSpawnedTasksInline(admin.TabularInline):
    model = TaskSpawnSpawnedTasks


@admin.register(TaskSpawn)
class TaskSpawnAdmin(admin.ModelAdmin):
    inlines = [TaskSpawnSpawnedTasksInline]


class TaskConsolidationClosingTasksInline(admin.TabularInline):
    model = TaskConsolidationClosingTasks


class TaskConsolidationSpawnedTasksInline(admin.TabularInline):
    model = TaskConsolidationSpawnedTasks


@admin.register(TaskConsolidation)
class TaskConsolidationAdmin(admin.ModelAdmin):
    inlines = [TaskConsolidationClosingTasksInline, TaskConsolidationSpawnedTasksInline]


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    pass


@admin.register(Commit)
class CommitAdmin(admin.ModelAdmin):
    actions = [spawn_and_consolidate_jobs]


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
