from django import forms
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from iris.app.models import Worker


class BrowserDateInput(forms.DateTimeInput):
    input_type = "datetime-local"


class CancelItemsViewForm(forms.Form):
    reason = forms.CharField(label=_("Reason"))
    datetime = forms.DateTimeField(
        label=_("Date/Time"), widget=BrowserDateInput(), initial=now
    )


class WorkerModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.user.username


class AddCommitTasksViewForm(forms.Form):
    worker = WorkerModelChoiceField(queryset=Worker.objects.all())


class AddDelayTasksViewForm(forms.Form):
    worker = WorkerModelChoiceField(queryset=Worker.objects.all())
    duration = forms.DurationField()


class AddSuspendTasksViewForm(forms.Form):
    worker = WorkerModelChoiceField(queryset=Worker.objects.all())
