from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from django.views.generic.edit import ContextMixin, ModelFormMixin, SingleObjectMixin

from iris.app.forms import CancelItemForm, CreateItemModelForm, DelayModelForm
from iris.app.models import (
    Commit,
    Delay,
    Item,
    NotCanceledError,
    Process,
    Station,
    Suspension,
    Task,
    Worker,
)


class PageModeMixin(ContextMixin):
    default_mode = 0
    page_modes = ["default"]
    page_mode_param = "mode"

    @property
    def current_mode(self):
        try:
            query_mode = self.request.GET[self.page_mode_param]
        except KeyError:
            return self.page_modes[self.default_mode]
        else:
            if query_mode in self.page_modes:
                return query_mode
            else:
                return self.page_modes[self.default_mode]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_mode"] = self.current_mode
        return context


class NextUrlParamMixin:
    next_url_param = "next"

    def get_next_url(self):
        if self.next_url_param in self.request.GET:
            return self.request.GET[self.next_url_param]


class NextUrlFieldMixin(NextUrlParamMixin, ModelFormMixin):
    next_url_field = "next_url"

    def get_next_url(self):
        if self.next_url_field in self.request.POST:
            return self.request.GET[self.next_url_field]
        else:
            return super().get_next_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next_url"] = self.get_next_url()
        return context

    def get_success_url(self):
        next_url = self.get_next_url()
        return next_url if next_url is not None else super().get_success_url()


class SomePermissionRequiredMixin(PermissionRequiredMixin):
    def has_permission(self):
        perms = self.get_permission_required()
        return any([self.request.user.has_perm(perm) for perm in perms])


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "iris/index.html"


class IrisLoginView(LoginView):
    next_page = reverse_lazy("iris:index")


class IrisLogoutView(LogoutView):
    next_page = reverse_lazy("iris:index")


class StationView(LoginRequiredMixin, PageModeMixin, DetailView):
    template_name = "iris/screens/station.html"
    model = Station
    page_modes = ["pending", "delayed", "suspended"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        station = self.get_object()
        if self.current_mode == "pending":
            context["tasks"] = Task.objects.pending(station=station)
        elif self.current_mode == "delayed":
            context["tasks"] = Task.objects.delayed(station=station)
        elif self.current_mode == "suspended":
            context["tasks"] = Task.objects.suspended(station=station)
        return context


class TaskListView(PageModeMixin, ListView):
    template_name = "iris/screens/tasks.html"
    model = Task
    page_modes = ["pending", "delayed", "suspended", "completed"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.current_mode == "pending":
            context["tasks"] = Task.objects.pending()
        elif self.current_mode == "delayed":
            context["tasks"] = Task.objects.delayed()
        elif self.current_mode == "suspended":
            context["tasks"] = Task.objects.suspended()
        elif self.current_mode == "completed":
            context["tasks"] = Task.objects.completed()
        return context


class ItemListView(LoginRequiredMixin, PageModeMixin, ListView):
    template_name = "iris/screens/items.html"
    model = Item
    page_modes = ["pending", "completed", "canceled"]

    def get_queryset(self):
        if self.current_mode == "pending":
            return Item.objects.pending()
        elif self.current_mode == "completed":
            return Item.objects.completed()
        elif self.current_mode == "canceled":
            return Item.objects.canceled()
        return super().get_queryset()


class IssuesView(SomePermissionRequiredMixin, PageModeMixin, TemplateView):
    template_name = "iris/screens/issues.html"
    permission_required = (
        "iris.view_delay",
        "iris.view_suspension",
    )
    page_modes = ["both", "delays", "suspensions"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.current_mode in ["both", "delays"]:
            context |= {
                "delays": Delay.objects.in_effect(),
            }
        if self.current_mode in ["both", "suspensions"]:
            context |= {
                "suspensions": Suspension.objects.in_effect(),
            }
        return context


class TaskDetailView(DetailView):
    template_name = "iris/detail/task.html"
    model = Task

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            station_pk = self.request.GET["station"]
            _station = Station.objects.get(pk=station_pk)
        except KeyError:
            pass
        except Station.DoesNotExist:
            pass
        else:
            context["station_pk"] = station_pk
        return context


class CreateForTaskMixin(LoginRequiredMixin, NextUrlFieldMixin, CreateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["task"] = Task.objects.get(pk=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        form.instance.task = Task.objects.get(pk=self.kwargs["pk"])
        form.instance.worker = Worker.objects.get(user=self.request.user)
        return super().form_valid(form)


class CreateCommitForTaskView(CreateForTaskMixin, PermissionRequiredMixin, CreateView):
    template_name = "iris/forms/create_commit_for_task.html"
    model = Commit
    permission_required = "iris.add_commit"
    fields = ["notes"]

    def post(self, *args, **kwargs):
        returned = super().post(*args, **kwargs)
        self.object.spawn_and_consolidate_tasks()
        return returned


class CreateDelayForTaskView(CreateForTaskMixin, PermissionRequiredMixin, CreateView):
    template_name = "iris/forms/create_delay_for_task.html"
    model = Delay
    form_class = DelayModelForm
    permission_required = "iris.add_delay"


class CommitFormView(PermissionRequiredMixin, NextUrlFieldMixin, UpdateView):
    template_name = "iris/forms/edit_commit.html"
    model = Commit
    permission_required = "iris.change_commit"
    fields = ["notes"]


class DelayFormView(PermissionRequiredMixin, NextUrlFieldMixin, UpdateView):
    template_name = "iris/forms/edit_delay.html"
    model = Delay
    form_class = DelayModelForm
    permission_required = "iris.change_delay"


class DelayEndView(
    PermissionRequiredMixin,
    SingleObjectMixin,
    NextUrlParamMixin,
    View,
):
    model = Delay
    permission_required = "iris.change_delay"

    def get(self, request, *args, **kwargs):
        self.get_object().end()
        return HttpResponseRedirect(self.get_next_url())


class CreateSuspensionForTaskView(
    CreateForTaskMixin, PermissionRequiredMixin, CreateView
):
    template_name = "iris/forms/create_suspension_for_task.html"
    model = Suspension
    permission_required = "iris.add_suspension"
    fields = ["notes"]


class SuspensionFormView(PermissionRequiredMixin, NextUrlFieldMixin, UpdateView):
    template_name = "iris/forms/edit_suspension.html"
    model = Suspension
    permission_required = "iris.change_suspension"
    fields = ["notes"]


class SuspensionLiftView(
    PermissionRequiredMixin,
    SingleObjectMixin,
    NextUrlParamMixin,
    View,
):
    model = Suspension
    permission_required = "iris.change_suspension"

    def get(self, request, *args, **kwargs):
        self.get_object().lift()
        return HttpResponseRedirect(self.get_next_url())


class ItemFormView(PermissionRequiredMixin, NextUrlFieldMixin, UpdateView):
    template_name = "iris/forms/edit_item.html"
    model = Item
    permission_required = "iris.change_item"
    fields = ["description", "notes"]


class CreateItemView(PermissionRequiredMixin, NextUrlFieldMixin, CreateView):
    template_name = "iris/forms/create_item.html"
    model = Item
    permission_required = "iris.add_item"
    form_class = CreateItemModelForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["processes"] = Process.objects.all().values("pk", "name")
        return context


class CancelItemView(PermissionRequiredMixin, NextUrlFieldMixin, UpdateView):
    template_name = "iris/forms/cancel_item.html"
    model = Item
    permission_required = "iris.change_item"
    form_class = CancelItemForm


class RestoreItemView(PermissionRequiredMixin, NextUrlParamMixin, View):
    permission_required = "iris.change_item"

    def get(self, request, *args, **kwargs):
        try:
            item_pk = self.kwargs["pk"]
            object = Item.objects.get(pk=item_pk)
            object.restore()
        except Item.DoesNotExist:
            messages.error(request, _("The item does not exists."))
            return HttpResponseRedirect(self.get_next_url())
        except NotCanceledError:
            messages.error(request, _("The item is not cancelled."))
            return HttpResponseRedirect(self.get_next_url())
        messages.info(request, _("The item was restored."))
        return HttpResponseRedirect(self.get_next_url())
