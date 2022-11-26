from django.db.models import F, Manager, Max, Q
from django.utils.timezone import now


class JobManager(Manager):
    def pending(self, station=None):
        queryset = self.get_queryset()
        if station is not None:
            queryset = queryset.filter(task__stations=station)
        return (
            queryset.filter(commit__isnull=True, work__cancel_time__isnull=True)
            .annotate(
                max_delay=Max(F("delays__created") + F("delays__duration")),
            )
            .filter(Q(max_delay__isnull=True) | (Q(max_delay__lt=now())))
            .exclude(
                Q(suspensions__isnull=False) & Q(suspensions__lifted_at__isnull=True)
            )
        )

    def canceled(self, station=None):
        queryset = self.get_queryset()
        if station is not None:
            queryset = queryset.filter(task__stations=station)
        return queryset.filter(work__cancel_time__isnull=False)

    def completed(self, station=None):
        queryset = self.get_queryset()
        if station is not None:
            queryset = queryset.filter(task__stations=station)
        return queryset.filter(commit__isnull=False)

    def delayed(self, station=None):
        queryset = self.get_queryset()
        if station is not None:
            queryset = queryset.filter(task__stations=station)
        return queryset.annotate(
            max_delay=Max(F("delays__created") + F("delays__duration")),
        ).filter(Q(max_delay__isnull=False) | (Q(max_delay__gt=now())))

    def suspended(self, station=None):
        queryset = self.get_queryset()
        if station is not None:
            queryset = queryset.filter(task__stations=station)
        return queryset.filter(Q(suspensions__lifted_at__isnull=True))


class DelayManager(Manager):
    def in_effect(self, station=None):
        queryset = self.get_queryset()
        if station is not None:
            queryset = queryset.filter(job__task__stations=station)
        return queryset.annotate(
            delay_limit=F("created") + F("duration"),
        ).filter(delay_limit__gt=now())


class SuspensionManager(Manager):
    def in_effect(self, station=None):
        queryset = self.get_queryset()
        if station is not None:
            queryset = queryset.filter(job__task__stations=station)
        return queryset.filter(Q(lifted_at__isnull=True))
