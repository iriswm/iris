from django.contrib import admin, messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.edit import FormView

from iris.app.admin.forms import CancelItemsViewForm
from iris.app.models import AlreadyCanceledError, Item


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


class CancelItemsView(AdminContextMixin, PermissionRequiredMixin, FormView):
    permission_required = "iris.change_item"
    template_name = "admin/iris/item/cancel_items.html"
    form_class = CancelItemsViewForm
    success_url = reverse_lazy("admin:iris_item_changelist")

    def get(self, request, *args, **kwargs):
        ids = self.request.GET["ids"]
        items = Item.objects.filter(pk__in=ids.split(","))
        for item in items:
            if item.canceled:
                messages.error(
                    self.request,
                    _("The item '{item_name}' is already canceled.").format(
                        item_name=str(item),
                    ),
                )
                return HttpResponseRedirect(reverse("admin:iris_item_changelist"))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ids = self.request.GET["ids"]
        items = Item.objects.filter(pk__in=ids.split(","))
        return {
            **super().get_context_data(**kwargs),
            "title": _("Cancel items"),
            "ids": ids,
            "items": items,
        }

    def form_valid(self, form):
        ids = self.request.GET["ids"]
        items = Item.objects.filter(pk__in=ids.split(","))
        reason = form.cleaned_data["reason"]
        datetime_ = form.cleaned_data["datetime"]
        try:
            with transaction.atomic():
                for item in items:
                    item.cancel(reason, datetime_)
        except AlreadyCanceledError as e:
            messages.error(self.request, str(e))
            return HttpResponseRedirect(reverse("admin:cancel_items") + f"?ids={ids}")
        else:
            messages.info(self.request, _("The items were canceled."))
            return super().form_valid(form)
