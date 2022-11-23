from django.contrib import admin, messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.edit import FormView

from iris.app.admin.forms import CancelWorksViewForm
from iris.app.models import Work


class AlreadyCanceledError(Exception):
    pass


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


class CancelWorksView(AdminContextMixin, PermissionRequiredMixin, FormView):
    permission_required = "iris.change_work"
    template_name = "admin/iris/work/cancel_works.html"
    form_class = CancelWorksViewForm
    success_url = reverse_lazy("admin:iris_work_changelist")

    def get(self, request, *args, **kwargs):
        ids = self.request.GET["ids"]
        works = Work.objects.filter(pk__in=ids.split(","))
        for work in works:
            if work.canceled:
                messages.error(
                    self.request,
                    _("The work '{work_name}' is already canceled.").format(
                        work_name=str(work),
                    ),
                )
                return HttpResponseRedirect(reverse("admin:iris_work_changelist"))
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
                    if work.canceled:
                        messages.error(
                            self.request,
                            _("The work '{work_name}' is already canceled.").format(
                                work_name=str(work),
                            ),
                        )
                        raise AlreadyCanceledError()
                    else:
                        work.cancel(reason, datetime_)
        except AlreadyCanceledError:
            return HttpResponseRedirect(reverse("admin:cancel_works") + f"?ids={ids}")
        messages.info(self.request, _("The works were canceled."))
        return super().form_valid(form)
