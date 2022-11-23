from django.urls import path

from iris.app.views import (
    AlertsView,
    IndexView,
    IrisLoginView,
    IrisLogoutView,
    StationView,
)

app_name = "iris"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", IrisLoginView.as_view(), name="login"),
    path("logout/", IrisLogoutView.as_view(), name="logout"),
    path("station/<int:pk>/", StationView.as_view(), name="station"),
    path("alerts/", AlertsView.as_view(), name="alerts"),
]
