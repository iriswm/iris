from django.contrib import admin
from django.urls import path
from django.utils.translation import gettext_lazy as _

from iris.app.admin.actions import (
    cancel_works,
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


@admin.register(Work)
class WorkAdmin(CompletableAdminMixin, CancelableAdminMixin, admin.ModelAdmin):
    actions = [cancel_works, restore_works, spawn_jobs]
    list_display = ["__str__", "completed", "canceled"]

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


@admin.register(Job)
class JobAdmin(CompletableAdminMixin, admin.ModelAdmin):
    list_display = ["__str__", "completed"]


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
    pass
