from django.db.models import F, Manager, Q
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


class DelayManager(Manager):
    def current(self, station=None):
        queryset = self.get_queryset()
        if station is not None:
            queryset = queryset.filter(job__task__stations=station)
        return queryset.annotate(
            delay_limit=F("created") + F("duration"),
        ).filter(delay_limit__gt=now())


class SuspensionManager(Manager):
    def current(self, station=None):
        queryset = self.get_queryset()
        if station is not None:
            queryset = queryset.filter(job__task__stations=station)
        return queryset.filter(Q(lifted_at__isnull=True) | Q(lifted_at__gt=now()))
