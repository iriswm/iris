from django.contrib import admin

from iris.app.models import (
    Category,
    CategorySpawnedTasks,
    Commit,
    Delay,
    Job,
    NoteTemplate,
    Priority,
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


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    pass


class CategorySpawnedTasksInline(admin.TabularInline):
    model = CategorySpawnedTasks


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = [CategorySpawnedTasksInline]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    pass


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    pass


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
    pass


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


@admin.register(Priority)
class PriorityAdmin(admin.ModelAdmin):
    pass
