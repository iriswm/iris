from datetime import timedelta

from django import forms
from django.core.validators import ValidationError
from django.utils.timezone import now
from django.utils.translation import gettext as _

from iris.app.models import Delay, Item


class DelayModelForm(forms.ModelForm):
    days = forms.IntegerField(min_value=0, required=True)
    hours = forms.IntegerField(min_value=0, required=True)
    minutes = forms.IntegerField(min_value=0, required=True)

    class Meta:
        model = Delay
        fields = ["notes"]

    def __init__(self, *args, **kwargs):
        instance = kwargs["instance"]
        if instance is not None:
            remainder = int(instance.duration.total_seconds())
            days = kwargs["initial"]["days"] = remainder // 86400
            remainder -= days * 86400
            hours = kwargs["initial"]["hours"] = remainder // 3600
            remainder -= hours * 3600
            minutes = kwargs["initial"]["minutes"] = remainder // 60
            remainder -= minutes * 60
            kwargs["initial"].update(
                {
                    "days": days,
                    "hours": hours,
                    "minutes": minutes,
                }
            )
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        try:
            duration = timedelta(
                days=cleaned_data["days"],
                hours=cleaned_data["hours"],
                minutes=cleaned_data["minutes"],
            )
        except KeyError:
            raise ValidationError(_("Delays must have a duration."), code="invalid")
        else:
            if duration == timedelta():
                raise ValidationError(_("Delays must have a duration."), code="invalid")

    def save(self):
        self.instance.duration = timedelta(
            days=self.cleaned_data["days"],
            hours=self.cleaned_data["hours"],
            minutes=self.cleaned_data["minutes"],
        )
        return super().save()


class CreateItemModelForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["process", "description", "notes", "quantity"]

    def save(self):
        instance = super().save()
        instance.spawn_tasks()
        return instance


class CancelItemForm(forms.ModelForm):
    reason = forms.CharField(required=True)
    time = forms.DateTimeField(required=True, initial=now)

    class Meta:
        model = Item
        fields = []

    def save(self):
        self.instance.cancel(
            self.cleaned_data["reason"],
            self.cleaned_data["time"],
        )
        return super().save()
