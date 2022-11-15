from iris.app.models import Station


def stations(request):
    return {
        "stations": Station.objects.all(),
    }
