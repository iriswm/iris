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

from iris.app.forms import CreateWorkModelForm, DelayModelForm
from iris.app.models import (
    Category,
    Commit,
    Delay,
    Job,
    Station,
    Suspension,
    Work,
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
    model = Station
    page_modes = ["pending", "delayed", "suspended"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        station = self.get_object()
        if self.current_mode == "pending":
            context["jobs"] = Job.objects.pending(station=station)
        elif self.current_mode == "delayed":
            context["jobs"] = Job.objects.delayed(station=station)
        elif self.current_mode == "suspended":
            context["jobs"] = Job.objects.suspended(station=station)
        return context


class JobListView(PageModeMixin, ListView):
    model = Job
    page_modes = ["pending", "delayed", "suspended", "completed"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.current_mode == "pending":
            context["jobs"] = Job.objects.pending()
        elif self.current_mode == "delayed":
            context["jobs"] = Job.objects.delayed()
        elif self.current_mode == "suspended":
            context["jobs"] = Job.objects.suspended()
        elif self.current_mode == "completed":
            context["jobs"] = Job.objects.completed()
        return context


class WorkListView(LoginRequiredMixin, PageModeMixin, ListView):
    model = Work
    page_modes = ["pending", "completed", "canceled"]

    def get_queryset(self):
        if self.current_mode == "pending":
            return Work.objects.pending()
        elif self.current_mode == "completed":
            return Work.objects.completed()
        elif self.current_mode == "canceled":
            return Work.objects.canceled()
        return super().get_queryset()


class AlertsView(SomePermissionRequiredMixin, PageModeMixin, TemplateView):
    template_name = "iris/alerts.html"
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


class JobDetailView(DetailView):
    model = Job

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


class CreateForJobMixin(LoginRequiredMixin, NextUrlFieldMixin, CreateView):
    template_name_suffix = "_create_for_job"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["job"] = Job.objects.get(pk=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        form.instance.job = Job.objects.get(pk=self.kwargs["pk"])
        form.instance.worker = Worker.objects.get(user=self.request.user)
        return super().form_valid(form)


class CreateCommitForJobView(CreateForJobMixin, PermissionRequiredMixin, CreateView):
    model = Commit
    permission_required = "iris.add_commit"
    fields = ["notes"]


class CreateDelayForJobView(CreateForJobMixin, PermissionRequiredMixin, CreateView):
    model = Delay
    form_class = DelayModelForm
    permission_required = "iris.add_delay"


class CommitFormView(PermissionRequiredMixin, NextUrlFieldMixin, UpdateView):
    model = Commit
    permission_required = "iris.change_commit"
    fields = ["notes"]


class DelayFormView(PermissionRequiredMixin, NextUrlFieldMixin, UpdateView):
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


class CreateSuspensionForJobView(
    CreateForJobMixin, PermissionRequiredMixin, CreateView
):
    model = Suspension
    permission_required = "iris.add_suspension"
    fields = ["notes"]


class SuspensionFormView(PermissionRequiredMixin, NextUrlFieldMixin, UpdateView):
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


class WorkFormView(PermissionRequiredMixin, NextUrlFieldMixin, UpdateView):
    model = Work
    permission_required = "iris.change_work"
    fields = ["description", "notes"]


class CreateWorkView(PermissionRequiredMixin, NextUrlFieldMixin, CreateView):
    template_name_suffix = "_create"
    model = Work
    permission_required = "iris.add_work"
    form_class = CreateWorkModelForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all().values("pk", "name")
        return context
