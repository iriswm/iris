from django.contrib import admin, messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from iris.app.admin.forms import CancelItemsViewForm
from iris.app.models import AlreadyCanceledError, Commit, Item, Task


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


class ItemCancelView(AdminContextMixin, PermissionRequiredMixin, FormView):
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
            return HttpResponseRedirect(self.request.path_info + f"?ids={ids}")
        else:
            messages.info(self.request, _("The items were canceled."))
            return super().form_valid(form)


class ConfirmationViewMixin(AdminContextMixin, PermissionRequiredMixin, TemplateView):
    template_name = "admin/iris/confirmation.html"
    confirmation_title = ""
    confirmation_text = ""

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "title": self.confirmation_title,
            "confirmation_text": self.confirmation_text,
        }

    def confirmed(self, request):
        return bool(request.POST.get("confirm"))

    def confirm_again(self, request):
        ids = request.GET["ids"]
        messages.error(
            request, str(_("You have to check the confirmation box to continue."))
        )
        return HttpResponseRedirect(request.path_info + f"?ids={ids}")


class ItemSpawnTasksView(ConfirmationViewMixin):
    permission_required = "iris.add_task"
    confirmation_title = _lazy("Confirm tasks creation")
    confirmation_text = _lazy(
        "There are tasks already created for one or more of the selected items. "
        "Are you sure you want to proceed?"
    )

    @staticmethod
    def get_ids_and_items(request):
        ids = request.GET["ids"]
        items = Item.objects.filter(pk__in=ids.split(","))
        return ids, items

    def get(self, request, *args, **kwargs):
        _ids, items = self.get_ids_and_items(request)
        for item in items:
            if item.tasks.count() > 0:
                return super().get(request, *args, **kwargs)
        return self.apply(request)

    def get_context_data(self, **kwargs):
        ids, items = self.get_ids_and_items(self.request)
        return {
            **super().get_context_data(**kwargs),
            "ids": ids,
            "objects": items,
        }

    def post(self, request):
        if not self.confirmed(request):
            return self.confirm_again(request)
        return self.apply(request)

    def apply(self, request):
        _ids, items = self.get_ids_and_items(request)
        try:
            with transaction.atomic():
                for item in items:
                    item.spawn_tasks()
        except NoProcessError as e:
            messages.error(request, str(e))
        else:
            messages.info(request, _("Tasks spawned."))
        return HttpResponseRedirect(reverse("admin:iris_item_changelist"))


class CommitSpawnAndConsolidateTasksView(ConfirmationViewMixin):
    permission_required = "iris.add_task"
    confirmation_title = _lazy("Confirm tasks creation")
    confirmation_text = _lazy(
        "There are tasks already derived from one or more of the selected commits. "
        "Are you sure you want to proceed?"
    )

    @staticmethod
    def get_ids_and_commits(request):
        ids = request.GET["ids"]
        commits = Commit.objects.filter(pk__in=ids.split(","))
        return ids, commits

    def get(self, request, *args, **kwargs):
        _ids, commits = self.get_ids_and_commits(request)
        for commit in commits:
            potential_transitions = commit.task.step_transition.required_by.all()
            potential_tasks = Task.objects.filter(
                item=commit.task.item, step_transition__in=potential_transitions
            )
            if potential_tasks.count() > 0:
                return super().get(request, *args, **kwargs)
        return self.apply(request)

    def get_context_data(self, **kwargs):
        ids, commits = self.get_ids_and_commits(self.request)
        return {
            **super().get_context_data(**kwargs),
            "ids": ids,
            "objects": commits,
        }

    def post(self, request):
        if not self.confirmed(request):
            return self.confirm_again(request)
        return self.apply(request)

    def apply(self, request):
        _ids, commits = self.get_ids_and_commits(request)
        with transaction.atomic():
            for commit in commits:
                commit.spawn_and_consolidate_tasks()
        messages.info(request, _("Tasks spawned."))
        return HttpResponseRedirect(reverse("admin:iris_commit_changelist"))
