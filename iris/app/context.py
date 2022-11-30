from django.utils.translation import get_language

from iris.app.models import Station


def stations(request):
    return {
        "stations": Station.objects.all(),
    }


def current_language(request):
    current_language = get_language()
    return (
        {
            "current_language": current_language,
        }
        if current_language is not None
        else {}
    )
