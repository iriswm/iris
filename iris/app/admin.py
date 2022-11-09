from django.contrib import admin, messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.urls import path, reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormView

from .forms import CancelWorksViewForm
from .models import (
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


class AdminContextMixin:
    def get_context_data(self, **kwargs):
        context = {
            **super().get_context_data(**kwargs),
            **admin.site.each_context(self.request),
        }
        if hasattr(self, "model"):
            context |= {
                "opts": self.model._meta,
            }
        return context


class AlreadyCancelledError(Exception):
    pass


class AlreadyRestoredError(Exception):
    pass


class CancelWorksView(AdminContextMixin, PermissionRequiredMixin, FormView):
    permission_required = "iris.change_work"
    template_name = "admin/iris/work/cancel_works.html"
    form_class = CancelWorksViewForm
    success_url = reverse_lazy("admin:iris_work_changelist")

    def get(self, request, *args, **kwargs):
        ids = self.request.GET["ids"]
        works = Work.objects.filter(pk__in=ids.split(","))
        for work in works:
            if work.cancelled:
                messages.error(
                    self.request, _(f"The work '{work}' is already cancelled.")
                )
                return HttpResponseRedirect(reverse_lazy("admin:iris_work_changelist"))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ids = self.request.GET["ids"]
        works = Work.objects.filter(pk__in=ids.split(","))
        return {
            **super().get_context_data(**kwargs),
            "title": _("Cancel works"),
            "ids": ids,
            "works": works,
        }

    def form_valid(self, form):
        ids = self.request.GET["ids"]
        works = Work.objects.filter(pk__in=ids.split(","))
        reason = form.cleaned_data["reason"]
        datetime_ = form.cleaned_data["datetime"]
        try:
            with transaction.atomic():
                for work in works:
                    if work.cancelled:
                        messages.error(
                            self.request, _(f"The work '{work}' is already cancelled.")
                        )
                        raise AlreadyCancelledError()
                    else:
                        work.cancel(reason, datetime_)
        except AlreadyCancelledError:
            return HttpResponseRedirect(
                reverse_lazy("admin:cancel_works") + f"?ids={ids}"
            )
        messages.info(self.request, _("The works were cancelled."))
        return super().form_valid(form)


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    actions = ["cancel_works", "restore_works"]

    @admin.action(description=str(_("Cancel selected works")))
    def cancel_works(self, request, queryset):
        selected = queryset.values_list("pk", flat=True)
        selected_joined = ",".join(str(pk) for pk in selected)
        return HttpResponseRedirect(
            reverse_lazy("admin:cancel_works") + f"?ids={selected_joined}"
        )

    @admin.action(description=str(_("Restore selected works")))
    def restore_works(self, request, queryset):
        selected = queryset.values_list("pk", flat=True)
        selected_joined = ",".join(str(pk) for pk in selected)
        try:
            with transaction.atomic():
                for work in queryset.all():
                    if not work.cancelled:
                        messages.error(
                            request, _(f"The work '{work}' is already restored.")
                        )
                        raise AlreadyRestoredError()
                    else:
                        work.restore()
        except AlreadyRestoredError:
            return HttpResponseRedirect(reverse_lazy("admin:iris_work_changelist"))
        messages.info(request, _("The works were restored."))
        return HttpResponseRedirect(reverse("admin:iris_work_changelist"))

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
