from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView
from django.views.generic.base import TemplateView

from iris.app.models import Commit, Delay, Job, Station, Suspension


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


class SomePermissionRequiredMixin(PermissionRequiredMixin):
    def has_permission(self):
        perms = self.get_permission_required()
        return any([self.request.user.has_perm(perm) for perm in perms])


class AlertsView(SomePermissionRequiredMixin, TemplateView):
    template_name = "iris/alerts.html"
    permission_required = (
        "iris.view_delay",
        "iris.view_suspension",
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context |= {
            "delays": Delay.objects.all(),
            "suspensions": Suspension.objects.all(),
        }
        return context


class JobDetailView(DetailView):
    model = Job


class CreateCommitView(CreateView):
    model = Commit


class CreateDelayView(CreateView):
    model = Delay


class CreateSuspensionView(CreateView):
    model = Suspension
