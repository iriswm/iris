from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from iris.app.forms import CreateDelayForm
from iris.app.models import Commit, Delay, Job, Station, Suspension, Work, Worker


class PageModeMixin:
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


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "iris/index.html"


class IrisLoginView(LoginView):
    next_page = reverse_lazy("iris:index")


class IrisLogoutView(LogoutView):
    next_page = reverse_lazy("iris:index")


class StationView(LoginRequiredMixin, DetailView):
    model = Station

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        station = self.get_object()
        context["jobs"] = Job.objects.pending(station=station)
        return context


class WorkListView(ListView):
    model = Work


class JobListView(ListView):
    model = Job


class SomePermissionRequiredMixin(PermissionRequiredMixin):
    def has_permission(self):
        perms = self.get_permission_required()
        return any([self.request.user.has_perm(perm) for perm in perms])


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


class JobItemCreateViewMixin(LoginRequiredMixin, CreateView):
    def get_job_and_worker(self):
        job_pk = self.request.GET["job"]
        job = Job.objects.get(pk=job_pk)
        worker = Worker.objects.get(user=self.request.user)
        return job, worker

    def get(self, *args, **kwargs):
        try:
            self.get_job_and_worker()
        except KeyError:
            messages.error(self.request, _("A job is required in this view."))
            return HttpResponseRedirect(reverse("iris:index"))
        except Job.DoesNotExist:
            messages.error(self.request, _("An existing job is required in this view."))
            return HttpResponseRedirect(reverse("iris:index"))
        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job, worker = self.get_job_and_worker()
        context["job"] = job
        return context

    def form_valid(self, form):
        job, worker = self.get_job_and_worker()
        form.instance.job = job
        form.instance.worker = worker
        return super().form_valid(form)

    def get_success_url(self):
        success_url = reverse("iris:index")
        try:
            station_pk = self.request.GET["station"]
            _station = Station.objects.get(pk=station_pk)
        except KeyError:
            pass
        except Station.DoesNotExist:
            pass
        else:
            success_url = reverse("iris:station", args=[station_pk])
        return success_url


class CreateCommitView(JobItemCreateViewMixin, PermissionRequiredMixin, CreateView):
    model = Commit
    permission_required = "iris.add_commit"
    fields = ["notes"]


class CreateDelayView(JobItemCreateViewMixin, PermissionRequiredMixin, CreateView):
    model = Delay
    form_class = CreateDelayForm
    permission_required = "iris.add_delay"

    def form_valid(self, form):
        form.instance.duration = timedelta(
            days=form.cleaned_data["days"],
            hours=form.cleaned_data["hours"],
            minutes=form.cleaned_data["minutes"],
        )
        return super().form_valid(form)


class CreateSuspensionView(JobItemCreateViewMixin, PermissionRequiredMixin, CreateView):
    model = Suspension
    permission_required = "iris.add_suspension"
    fields = ["notes"]
