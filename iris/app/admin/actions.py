from django.contrib import admin, messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from iris.app.models import NoProcessError, NotCanceledError, NotSuspendedError


@admin.action(description=str(_("Cancel selected items")))
def cancel_items(self, request, queryset):
    selected = queryset.values_list("pk", flat=True)
    selected_joined = ",".join(str(pk) for pk in selected)
    return HttpResponseRedirect(
        reverse("admin:cancel_items") + f"?ids={selected_joined}"
    )


@admin.action(description=str(_("Restore selected items")))
def restore_items(self, request, queryset):
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
def spawn_tasks(self, request, queryset):
    try:
        with transaction.atomic():
            for item in queryset.all():
                item.spawn_tasks()
    except NoProcessError as e:
        messages.error(request, str(e))
    else:
        messages.info(request, _("Tasks spawned."))
    return HttpResponseRedirect(reverse("admin:iris_item_changelist"))


@admin.action(description=str(_("Spawn and consolidate tasks")))
def spawn_and_consolidate_tasks(self, request, queryset):
    for commit in queryset.all():
        commit.spawn_and_consolidate_tasks()
    messages.info(request, _("Tasks spawned."))
    return HttpResponseRedirect(reverse("admin:iris_commit_changelist"))


@admin.action(description=str(_("Lift suspensions")))
def lift_suspensions(self, request, queryset):
    try:
        with transaction.atomic():
            for suspension in queryset.all():
                suspension.lift()
    except NotSuspendedError as e:
        messages.error(request, str(e))
    else:
        messages.info(request, _("Suspensions lifted."))
    return HttpResponseRedirect(reverse("admin:iris_suspension_changelist"))
