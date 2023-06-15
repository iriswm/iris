from django.db.models import Count, F, Max, Q, QuerySet
from django.utils.timezone import now


class ItemQuerySet(QuerySet):
    def pending(self):
        return (
            self.annotate(
                number_of_tasks=Count("tasks"), number_of_commits=Count("tasks__commit")
            )
            .filter(cancel_time__isnull=True)
            .exclude(number_of_tasks=F("number_of_commits"))
        )

    def completed(self):
        return self.annotate(
            number_of_tasks=Count("tasks"), number_of_commits=Count("tasks__commit")
        ).filter(number_of_tasks=F("number_of_commits"))

    def canceled(self):
        return self.filter(cancel_time__isnull=False)


class TaskQuerySet(QuerySet):
    def in_station(self, station):
        return self.filter(step_transition__creates__stations=station)

    def pending(self):
        return (
            self.filter(commit__isnull=True, item__cancel_time__isnull=True)
            .annotate(
                max_delay=Max(F("delays__created") + F("delays__duration")),
            )
            .filter(Q(max_delay__isnull=True) | (Q(max_delay__lt=now())))
            .exclude(
                Q(suspensions__isnull=False) & Q(suspensions__lifted_at__isnull=True)
            )
        )

    def completed(self):
        return self.filter(commit__isnull=False)

    def delayed(self):
        return self.annotate(
            max_delay=Max(F("delays__created") + F("delays__duration")),
        ).filter(Q(max_delay__isnull=False) & (Q(max_delay__gt=now())))

    def suspended(self):
        return self.filter(
            Q(suspensions__isnull=False) & Q(suspensions__lifted_at__isnull=True)
        )

    def with_issues(self):
        return self.annotate(
            max_delay=Max(F("delays__created") + F("delays__duration")),
        ).filter(
            Q(max_delay__isnull=False) & (Q(max_delay__gt=now()))
            | Q(suspensions__isnull=False) & Q(suspensions__lifted_at__isnull=True)
        )


class DelayQuerySet(QuerySet):
    def in_effect(self):
        return self.annotate(
            delay_limit=F("created") + F("duration"),
        ).filter(delay_limit__gt=now())


class SuspensionQuerySet(QuerySet):
    def in_effect(self):
        return self.filter(Q(lifted_at__isnull=True))
