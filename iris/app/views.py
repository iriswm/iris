from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "iris/base.html"


class IrisLoginView(LoginView):
    template_name = "iris/login.html"
    next_page = reverse_lazy("iris:index")


class IrisLogoutView(LogoutView):
    next_page = reverse_lazy("iris:index")
