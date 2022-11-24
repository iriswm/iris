from django.contrib import admin, messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from iris.app.models import NoCategoryError, NotCanceledError, NotSuspendedError


@admin.action(description=str(_("Cancel selected works")))
def cancel_works(self, request, queryset):
    selected = queryset.values_list("pk", flat=True)
    selected_joined = ",".join(str(pk) for pk in selected)
    return HttpResponseRedirect(
        reverse("admin:cancel_works") + f"?ids={selected_joined}"
    )


@admin.action(description=str(_("Restore selected works")))
def restore_works(self, request, queryset):
    try:
        with transaction.atomic():
            for work in queryset.all():
                work.restore()
    except NotCanceledError as e:
        messages.error(request, str(e))
    else:
        messages.info(request, _("The works were restored."))
    return HttpResponseRedirect(reverse("admin:iris_work_changelist"))


@admin.action(description=str(_("Spawn category jobs")))
def spawn_jobs(self, request, queryset):
    try:
        with transaction.atomic():
            for work in queryset.all():
                work.spawn_jobs()
    except NoCategoryError as e:
        messages.error(request, str(e))
    else:
        messages.info(request, _("Jobs spawned."))
    return HttpResponseRedirect(reverse("admin:iris_work_changelist"))


@admin.action(description=str(_("Spawn and consolidate jobs")))
def spawn_and_consolidate_jobs(self, request, queryset):
    for commit in queryset.all():
        commit.spawn_and_consolidate_jobs()
    messages.info(request, _("Jobs spawned."))
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
