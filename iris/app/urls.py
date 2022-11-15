from django.urls import path

from iris.app.views import IndexView, IrisLoginView, IrisLogoutView, StationView

app_name = "iris"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", IrisLoginView.as_view(), name="login"),
    path("logout/", IrisLogoutView.as_view(), name="logout"),
    path("station/<int:pk>", StationView.as_view(), name="station"),
]
