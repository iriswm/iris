from django.contrib import admin, messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class NotCanceledError(Exception):
    pass


@admin.action(description=str(_("Cancel selected works")))
def cancel_works(self, request, queryset):
    selected = queryset.values_list("pk", flat=True)
    selected_joined = ",".join(str(pk) for pk in selected)
    return HttpResponseRedirect(
        reverse("admin:cancel_works") + f"?ids={selected_joined}"
    )


@admin.action(description=str(_("Restore selected works")))
def restore_works(self, request, queryset):
    selected = queryset.values_list("pk", flat=True)
    selected_joined = ",".join(str(pk) for pk in selected)
    try:
        with transaction.atomic():
            for work in queryset.all():
                if not work.canceled:
                    messages.error(
                        request,
                        _("The work '{work_name}' is not canceled.").format(
                            work_name=str(work),
                        ),
                    )
                    raise NotCanceledError()
                else:
                    work.restore()
    except NotCanceledError:
        return HttpResponseRedirect(reverse("admin:iris_work_changelist"))
    messages.info(request, _("The works were restored."))
    return HttpResponseRedirect(reverse("admin:iris_work_changelist"))


@admin.action(description=str(_("Spawn category jobs")))
def spawn_jobs(self, request, queryset):
    all_works = queryset.all()
    for work in all_works:
        if work.category is None:
            messages.error(
                request,
                _("Work '{work_name}' doesn't have a category assigned.").format(
                    work_name=str(work),
                ),
            )
            return HttpResponseRedirect(reverse("admin:iris_work_changelist"))
    for work in all_works:
        work.spawn_jobs()
    messages.info(request, _("Jobs spawned."))
    return HttpResponseRedirect(reverse("admin:iris_work_changelist"))


@admin.action(description=str(_("Spawn and consolidate jobs")))
def spawn_and_consolidate_jobs(self, request, queryset):
    for commit in queryset.all():
        commit.spawn_and_consolidate_jobs()
    messages.info(request, _("Jobs spawned."))
    return HttpResponseRedirect(reverse("admin:iris_commit_changelist"))
