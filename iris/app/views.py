from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, RedirectURLMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from django.views.generic.edit import ContextMixin, SingleObjectMixin

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


class ContextRedirectURLMixin(RedirectURLMixin, ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                self.redirect_field_name: self.get_redirect_url(),
            }
        )
        return context


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "iris/index.html"


class IrisLoginView(LoginView):
    next_page = reverse_lazy("iris:index")


class IrisLogoutView(LogoutView):
    next_page = reverse_lazy("iris:index")


class BaseTaskListMixin(ListView):
    model = Task

    def get(self, request, status="pending"):
        self.status = status
        return super().get(request, status=status)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.status == "delayed":
            return queryset.delayed()
        elif self.status == "suspended":
            return queryset.suspended()
        elif self.status == "with_issues":
            return queryset.with_issues()
        elif self.status == "completed":
            return queryset.completed()
        else:
            return queryset.pending()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status"] = self.status
        return context


class StationTaskListView(BaseTaskListMixin, ListView):
    template_name = "iris/screens/station.html"

    def get(self, request, station, *args, **kwargs):
        self.station = Station.objects.get(pk=station)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.in_station(self.station)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["station"] = self.station
        return context


class GeneralTaskListView(BaseTaskListMixin, ListView):
    template_name = "iris/screens/tasks.html"


class TasksWithIssuesView(BaseTaskListMixin, ListView):
    template_name = "iris/screens/issues.html"

    def get(self, request, status="with_issues"):
        return super().get(request, status=status)


class ItemListView(LoginRequiredMixin, ListView):
    template_name = "iris/screens/items.html"
    model = Item

    def get(self, request, status="pending"):
        self.status = status
        return super().get(request, status=status)

    def get_queryset(self):
        if self.status == "completed":
            return Item.objects.completed()
        elif self.status == "canceled":
            return Item.objects.canceled()
        else:
            return Item.objects.pending()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status"] = self.status
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


class CreateForTaskMixin(LoginRequiredMixin, ContextRedirectURLMixin, CreateView):
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


class CommitFormView(PermissionRequiredMixin, ContextRedirectURLMixin, UpdateView):
    template_name = "iris/forms/edit_commit.html"
    model = Commit
    permission_required = "iris.change_commit"
    fields = ["notes"]


class DelayFormView(PermissionRequiredMixin, ContextRedirectURLMixin, UpdateView):
    template_name = "iris/forms/edit_delay.html"
    model = Delay
    form_class = DelayModelForm
    permission_required = "iris.change_delay"


class DelayEndView(
    PermissionRequiredMixin,
    SingleObjectMixin,
    ContextRedirectURLMixin,
    View,
):
    model = Delay
    permission_required = "iris.change_delay"

    def get(self, request, *args, **kwargs):
        self.get_object().end()
        return HttpResponseRedirect(self.get_redirect_url())


class CreateSuspensionForTaskView(
    CreateForTaskMixin, PermissionRequiredMixin, CreateView
):
    template_name = "iris/forms/create_suspension_for_task.html"
    model = Suspension
    permission_required = "iris.add_suspension"
    fields = ["notes"]


class SuspensionFormView(PermissionRequiredMixin, ContextRedirectURLMixin, UpdateView):
    template_name = "iris/forms/edit_suspension.html"
    model = Suspension
    permission_required = "iris.change_suspension"
    fields = ["notes"]


class SuspensionLiftView(
    PermissionRequiredMixin,
    SingleObjectMixin,
    ContextRedirectURLMixin,
    View,
):
    model = Suspension
    permission_required = "iris.change_suspension"

    def get(self, request, *args, **kwargs):
        self.get_object().lift()
        return HttpResponseRedirect(self.get_redirect_url())


class ItemFormView(PermissionRequiredMixin, ContextRedirectURLMixin, UpdateView):
    template_name = "iris/forms/edit_item.html"
    model = Item
    permission_required = "iris.change_item"
    fields = ["description", "notes"]


class CreateItemView(PermissionRequiredMixin, ContextRedirectURLMixin, CreateView):
    template_name = "iris/forms/create_item.html"
    model = Item
    permission_required = "iris.add_item"
    form_class = CreateItemModelForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["processes"] = Process.objects.all().values("pk", "name")
        return context


class CancelItemView(PermissionRequiredMixin, ContextRedirectURLMixin, UpdateView):
    template_name = "iris/forms/cancel_item.html"
    model = Item
    permission_required = "iris.change_item"
    form_class = CancelItemForm


class RestoreItemView(PermissionRequiredMixin, ContextRedirectURLMixin, View):
    permission_required = "iris.change_item"

    def get(self, request, *args, **kwargs):
        try:
            item_pk = self.kwargs["pk"]
            object = Item.objects.get(pk=item_pk)
            object.restore()
        except Item.DoesNotExist:
            messages.error(request, _("The item does not exists."))
            return HttpResponseRedirect(self.get_redirect_url())
        except NotCanceledError:
            messages.error(request, _("The item is not cancelled."))
            return HttpResponseRedirect(self.get_redirect_url())
        messages.info(request, _("The item was restored."))
        return HttpResponseRedirect(self.get_redirect_url())
