from django.contrib import admin

from iris.app.models import (
    Category,
    Commit,
    Delay,
    Job,
    NoteTemplate,
    Priority,
    Station,
    Suspension,
    Task,
    TaskConsolidation,
    TaskSpawn,
    Work,
    Worker,
)


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    pass


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    pass


@admin.register(TaskSpawn)
class TaskSpawnAdmin(admin.ModelAdmin):
    pass


@admin.register(TaskConsolidation)
class TaskConsolidationAdmin(admin.ModelAdmin):
    pass


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
