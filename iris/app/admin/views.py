from django.contrib import admin, messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from iris.app.admin.forms import (
    AddCommitTasksViewForm,
    AddDelayTasksViewForm,
    AddSuspendTasksViewForm,
    CancelItemsViewForm,
)
from iris.app.models import AlreadyCanceledError, Commit, Delay, Item, Suspension, Task


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
        with transaction.atomic():
            for item in items:
                item.spawn_tasks()
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


class AddActionsTaskViewMixin(AdminContextMixin, FormView):
    success_url = reverse_lazy("admin:iris_task_changelist")
    action_title = ""
    action_attr = ""
    action_verb = ""
    action_conflicts = []

    def get_context_data(self, **kwargs):
        ids = self.request.GET["ids"]
        tasks = Task.objects.filter(pk__in=ids.split(","))
        return {
            **super().get_context_data(**kwargs),
            "title": self.action_title,
            "ids": ids,
            "tasks": tasks,
        }

    def log_action_applied_message(self, task):
        messages.error(
            self.request,
            _("The task '{task_name}' is already {verb}.").format(
                task_name=str(task),
                verb=self.action_verb,
            ),
        )

    def log_action_conflicted_message(self, task, verb):
        messages.error(
            self.request,
            _("The task '{task_name}' is {verb}.").format(
                task_name=str(task),
                verb=verb,
            ),
        )

    def check_and_log(self, task):
        if getattr(task, self.action_attr):
            self.log_action_applied_message(task)
            return True
        for attr, verb in self.action_conflicts:
            if getattr(task, attr):
                self.log_action_conflicted_message(task, verb)
                return True
        return False

    def get_ids_and_tasks(self, request):
        ids = request.GET["ids"]
        return ids, Task.objects.filter(pk__in=ids.split(","))

    def get(self, request, *args, **kwargs):
        _ids, tasks = self.get_ids_and_tasks(request)
        for task in tasks:
            if self.check_and_log(task):
                return HttpResponseRedirect(reverse("admin:iris_task_changelist"))
        return super().get(request, *args, **kwargs)


class CommitTasksView(PermissionRequiredMixin, AddActionsTaskViewMixin):
    permission_required = "iris.add_commit"
    template_name = "admin/iris/task/commit_tasks.html"
    form_class = AddCommitTasksViewForm
    action_title = _lazy("Commit tasks")
    action_attr = "completed"
    action_verb = _lazy("completed")
    action_conflicts = [
        ("delayed", _lazy("delayed")),
        ("suspended", _lazy("suspended")),
    ]

    def form_valid(self, form):
        ids, tasks = self.get_ids_and_tasks(self.request)
        worker = form.cleaned_data["worker"]
        with transaction.atomic():
            for task in tasks:
                if self.check_and_log(task):
                    return HttpResponseRedirect(self.request.path_info + f"?ids={ids}")
            for task in tasks:
                Commit(task=task, worker=worker).save()
        messages.info(self.request, _("The tasks were commited."))
        return super().form_valid(form)


class DelayTasksView(PermissionRequiredMixin, AddActionsTaskViewMixin):
    permission_required = "iris.add_delay"
    template_name = "admin/iris/task/delay_tasks.html"
    form_class = AddDelayTasksViewForm
    action_title = _lazy("Delay tasks")
    action_attr = "delayed"
    action_verb = _lazy("delayed")
    action_conflicts = [
        ("completed", _lazy("completed")),
        ("suspended", _lazy("suspended")),
    ]

    def form_valid(self, form):
        ids, tasks = self.get_ids_and_tasks(self.request)
        worker = form.cleaned_data["worker"]
        duration = form.cleaned_data["duration"]
        with transaction.atomic():
            for task in tasks:
                if self.check_and_log(task):
                    return HttpResponseRedirect(self.request.path_info + f"?ids={ids}")
            for task in tasks:
                Delay(task=task, worker=worker, duration=duration).save()
        messages.info(self.request, _("The tasks were delayed."))
        return super().form_valid(form)


class SuspendTasksView(PermissionRequiredMixin, AddActionsTaskViewMixin):
    permission_required = "iris.add_suspension"
    template_name = "admin/iris/task/suspend_tasks.html"
    form_class = AddCommitTasksViewForm
    action_title = _lazy("Suspend tasks")
    action_attr = "suspended"
    action_verb = _lazy("suspended")
    action_conflicts = [
        ("completed", _lazy("completed")),
        ("delayed", _lazy("delayed")),
    ]

    def form_valid(self, form):
        ids, tasks = self.get_ids_and_tasks(self.request)
        worker = form.cleaned_data["worker"]
        with transaction.atomic():
            for task in tasks:
                if self.check_and_log(task):
                    return HttpResponseRedirect(self.request.path_info + f"?ids={ids}")
            for task in tasks:
                Suspension(task=task, worker=worker).save()
        messages.info(self.request, _("The tasks were suspended."))
        return super().form_valid(form)
