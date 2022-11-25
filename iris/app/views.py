from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, TemplateView

from iris.app.models import Commit, Delay, Job, Station, Suspension, Worker


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


class CreateCommitView(JobItemCreateViewMixin, CreateView):
    model = Commit
    fields = ["notes"]


class CreateDelayView(CreateView):
    model = Delay


class CreateSuspensionView(CreateView):
    model = Suspension
