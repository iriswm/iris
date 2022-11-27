from django.urls import path

from iris.app.views import (
    AlertsView,
    CommitFormView,
    CreateCommitForJobView,
    CreateDelayForJobView,
    CreateSuspensionForJobView,
    DelayEndView,
    DelayFormView,
    IndexView,
    IrisLoginView,
    IrisLogoutView,
    JobDetailView,
    JobListView,
    StationView,
    SuspensionFormView,
    SuspensionLiftView,
    WorkListView,
)

app_name = "iris"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", IrisLoginView.as_view(), name="login"),
    path("logout/", IrisLogoutView.as_view(), name="logout"),
    path("station/<int:pk>/", StationView.as_view(), name="station"),
    path("alerts/", AlertsView.as_view(), name="alerts"),
    path("jobs/", JobListView.as_view(), name="job_list"),
    path("job/<int:pk>/", JobDetailView.as_view(), name="job_detail"),
    path(
        "job/<int:pk>/commit/add/",
        CreateCommitForJobView.as_view(),
        name="job_add_commit",
    ),
    path(
        "job/<int:pk>/delay/add/", CreateDelayForJobView.as_view(), name="job_add_delay"
    ),
    path(
        "job/<int:pk>/suspension/add/",
        CreateSuspensionForJobView.as_view(),
        name="job_add_suspension",
    ),
    path(
        "commit/<int:pk>/change/",
        CommitFormView.as_view(),
        name="commit_change",
    ),
    path("delay/<int:pk>/change/", DelayFormView.as_view(), name="delay_change"),
    path("delay/<int:pk>/end/", DelayEndView.as_view(), name="delay_end"),
    path(
        "suspension/<int:pk>/change/",
        SuspensionFormView.as_view(),
        name="suspension_change",
    ),
    path(
        "suspension/<int:pk>/lift/",
        SuspensionLiftView.as_view(),
        name="suspension_lift",
    ),
    path("works/", WorkListView.as_view(), name="work_list"),
]
