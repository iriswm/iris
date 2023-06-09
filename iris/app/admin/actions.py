from django.contrib import admin, messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from iris.app.models import AlreadyEndedError, NotCanceledError, NotSuspendedError


@admin.action(description=str(_("Cancel selected items")))
def items_cancel(self, request, queryset):
    selected = queryset.values_list("pk", flat=True)
    selected_joined = ",".join(str(pk) for pk in selected)
    return HttpResponseRedirect(
        reverse("admin:iris_item_cancel") + f"?ids={selected_joined}"
    )


@admin.action(description=str(_("Restore selected items")))
def items_restore(self, request, queryset):
    try:
        with transaction.atomic():
            for item in queryset.all():
                item.restore()
    except NotCanceledError as e:
        messages.error(request, str(e))
    else:
        messages.info(request, _("The items were restored."))
    return HttpResponseRedirect(reverse("admin:iris_item_changelist"))


@admin.action(description=str(_("Spawn process tasks")))
def items_spawn_tasks(self, request, queryset):
    selected = queryset.values_list("pk", flat=True)
    selected_joined = ",".join(str(pk) for pk in selected)
    return HttpResponseRedirect(
        reverse("admin:iris_item_spawn_tasks") + f"?ids={selected_joined}"
    )


@admin.action(description=str(_("Spawn and consolidate tasks")))
def commits_spawn_tasks(self, request, queryset):
    selected = queryset.values_list("pk", flat=True)
    selected_joined = ",".join(str(pk) for pk in selected)
    return HttpResponseRedirect(
        reverse("admin:iris_commit_spawn_tasks") + f"?ids={selected_joined}"
    )


@admin.action(description=str(_("Lift suspensions")))
def suspensions_lift(self, request, queryset):
    try:
        with transaction.atomic():
            for suspension in queryset.all():
                suspension.lift()
    except NotSuspendedError as e:
        messages.error(request, str(e))
    else:
        messages.info(request, _("Suspensions lifted."))
    return HttpResponseRedirect(reverse("admin:iris_suspension_changelist"))


@admin.action(description=str(_("End delays now")))
def delays_end_now(self, request, queryset):
    try:
        with transaction.atomic():
            for delay in queryset.all():
                delay.end()
    except AlreadyEndedError as e:
        messages.error(request, str(e))
    else:
        messages.info(request, _("Delays ended."))
    return HttpResponseRedirect(reverse("admin:iris_delay_changelist"))


@admin.action(description=str(_("Commit the selected tasks")))
def tasks_commit_tasks(self, request, queryset):
    selected = queryset.values_list("pk", flat=True)
    selected_joined = ",".join(str(pk) for pk in selected)
    return HttpResponseRedirect(
        reverse("admin:iris_task_commit_tasks") + f"?ids={selected_joined}"
    )


@admin.action(description=str(_("Delay the selected tasks")))
def tasks_delay_tasks(self, request, queryset):
    selected = queryset.values_list("pk", flat=True)
    selected_joined = ",".join(str(pk) for pk in selected)
    return HttpResponseRedirect(
        reverse("admin:iris_task_delay_tasks") + f"?ids={selected_joined}"
    )


@admin.action(description=str(_("Suspend the selected tasks")))
def tasks_suspend_tasks(self, request, queryset):
    selected = queryset.values_list("pk", flat=True)
    selected_joined = ",".join(str(pk) for pk in selected)
    return HttpResponseRedirect(
        reverse("admin:iris_task_suspend_tasks") + f"?ids={selected_joined}"
    )
