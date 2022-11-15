from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import DetailView
from django.views.generic.base import TemplateView

from iris.app.models import Job, Station


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "iris/base.html"


class IrisLoginView(LoginView):
    template_name = "iris/login.html"
    next_page = reverse_lazy("iris:index")


class IrisLogoutView(LogoutView):
    next_page = reverse_lazy("iris:index")


class StationView(DetailView):
    model = Station
    template_name = "iris/station.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        station = self.get_object()
        context["jobs"] = [
            job
            for job in Job.objects.filter(task__stations=station).all()
            if not job.completed
        ]
        return context
