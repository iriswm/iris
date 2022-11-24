from django.db.models import F, Manager
from django.utils.timezone import now


class JobManager(Manager):
    def pending(self, station=None):
        queryset = self.get_queryset()
        if station is not None:
            queryset = queryset.filter(task__stations=station)
        return (
            queryset.filter(commit__isnull=True, work__cancel_time__isnull=True)
            .annotate(
                delays_limit=F("delays__created") + F("delays__duration"),
            )
            .exclude(delays__isnull=False, delays_limit__gt=now())
            .exclude(suspensions__isnull=False, suspensions__lifted_at__isnull=True)
            .exclude(suspensions__isnull=False, suspensions__lifted_at__gt=now())
        )
