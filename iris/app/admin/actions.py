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
                    messages.error(request, _(f"The work '{work}' is not canceled."))
                    raise NotCanceledError()
                else:
                    work.restore()
    except NotCanceledError:
        return HttpResponseRedirect(reverse("admin:iris_work_changelist"))
    messages.info(request, _("The works were restored."))
    return HttpResponseRedirect(reverse("admin:iris_work_changelist"))
