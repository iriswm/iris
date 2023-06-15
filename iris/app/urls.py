from django.urls import path

from iris.app.views import (
    CancelItemView,
    CommitFormView,
    CreateCommitForTaskView,
    CreateDelayForTaskView,
    CreateItemView,
    CreateSuspensionForTaskView,
    DelayEndView,
    DelayFormView,
    GeneralTaskListView,
    IndexView,
    IrisLoginView,
    IrisLogoutView,
    ItemFormView,
    ItemListView,
    RestoreItemView,
    StationTaskListView,
    SuspensionFormView,
    SuspensionLiftView,
    TaskDetailView,
    TasksWithIssuesView,
)

app_name = "iris"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", IrisLoginView.as_view(), name="login"),
    path("logout/", IrisLogoutView.as_view(), name="logout"),
    path("station/<int:station>", StationTaskListView.as_view(), name="station"),
    path(
        "station/<int:station>/<str:status>",
        StationTaskListView.as_view(),
        name="station",
    ),
    path("issues/", TasksWithIssuesView.as_view(), name="issues"),
    path("issues/<str:status>", TasksWithIssuesView.as_view(), name="issues"),
    path("tasks/", GeneralTaskListView.as_view(), name="task_list"),
    path("tasks/<str:status>", GeneralTaskListView.as_view(), name="task_list"),
    path("task/<int:pk>/", TaskDetailView.as_view(), name="task_detail"),
    path(
        "task/<int:pk>/commit/add/",
        CreateCommitForTaskView.as_view(),
        name="task_add_commit",
    ),
    path(
        "task/<int:pk>/delay/add/",
        CreateDelayForTaskView.as_view(),
        name="task_add_delay",
    ),
    path(
        "task/<int:pk>/suspension/add/",
        CreateSuspensionForTaskView.as_view(),
        name="task_add_suspension",
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
    path("items/", ItemListView.as_view(), name="item_list"),
    path("items/<str:status>", ItemListView.as_view(), name="item_list"),
    path("item/<int:pk>/change/", ItemFormView.as_view(), name="item_change"),
    path("item/<int:pk>/cancel/", CancelItemView.as_view(), name="item_cancel"),
    path("item/<int:pk>/restore/", RestoreItemView.as_view(), name="item_restore"),
    path("item/add/", CreateItemView.as_view(), name="item_add"),
]
