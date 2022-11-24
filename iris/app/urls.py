from django.urls import path

from iris.app.views import (
    AlertsView,
    CreateCommitView,
    CreateDelayView,
    CreateSuspensionView,
    IndexView,
    IrisLoginView,
    IrisLogoutView,
    JobDetailView,
    StationView,
)

app_name = "iris"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", IrisLoginView.as_view(), name="login"),
    path("logout/", IrisLogoutView.as_view(), name="logout"),
    path("station/<int:pk>/", StationView.as_view(), name="station"),
    path("alerts/", AlertsView.as_view(), name="alerts"),
    path("job/<int:pk>/", JobDetailView.as_view(), name="job_detail"),
    path("commit/add/", CreateCommitView.as_view(), name="commit_add"),
    path("delay/add/", CreateDelayView.as_view(), name="delay_add"),
    path("suspension/add/", CreateSuspensionView.as_view(), name="suspension_add"),
]
