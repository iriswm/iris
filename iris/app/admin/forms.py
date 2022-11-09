from django import forms
from django.utils.timezone import now


class BrowserDateInput(forms.DateTimeInput):
    input_type = "datetime-local"


class CancelWorksViewForm(forms.Form):
    reason = forms.CharField()
    datetime = forms.DateTimeField(widget=BrowserDateInput(), initial=now)
