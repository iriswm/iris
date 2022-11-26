from datetime import timedelta

from django import forms
from django.core.validators import ValidationError
from django.utils.translation import gettext as _

from iris.app.models import Delay


class CreateDelayForm(forms.ModelForm):
    days = forms.IntegerField(min_value=0, initial=0, required=False)
    hours = forms.IntegerField(min_value=0, initial=0, required=False)
    minutes = forms.IntegerField(min_value=0, initial=0, required=False)

    class Meta:
        model = Delay
        fields = ["notes"]

    def clean(self):
        cleaned_data = super().clean()
        try:
            duration = timedelta(
                days=cleaned_data["days"],
                hours=cleaned_data["hours"],
                minutes=cleaned_data["minutes"],
            )
        except:
            raise ValidationError(
                _("Can't calculate a valid delay duration."), code="invalid"
            )
        else:
            if duration == timedelta():
                raise ValidationError(
                    _("You can't create delays with no duration."), code="invalid"
                )
