from django import forms
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


class BrowserDateInput(forms.DateTimeInput):
    input_type = "datetime-local"


class CancelItemsViewForm(forms.Form):
    reason = forms.CharField(label=_("Reason"))
    datetime = forms.DateTimeField(
        label=_("Date/Time"), widget=BrowserDateInput(), initial=now
    )
