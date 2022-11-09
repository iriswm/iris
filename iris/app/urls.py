from django.urls import path

from iris.app.views import IndexView

app_name = "iris"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
]
