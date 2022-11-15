from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _
from django.views.static import serve

admin.site.site_header = _("Iris administration")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("iris.app.urls")),
]

if settings.DEBUG == True:
    urlpatterns.insert(
        0,
        re_path(
            "media/(?P<path>.*)",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    )
