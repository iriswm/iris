from django import forms


class BrowserDateInput(forms.DateInput):
    input_type = "datetime-local"


class CancelWorksViewForm(forms.Form):
    reason = forms.CharField()
    datetime = forms.DateTimeField(widget=BrowserDateInput(), required=False)
