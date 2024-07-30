from django import forms

from core.widgets import Wysiwyg

class CommunicatorProgramForm(forms.Form):
    custom_description = forms.CharField(widget=Wysiwyg(), required=False)
    jobs = forms.CharField(required=False)
    jobs_source = forms.CharField(widget=forms.Textarea(attrs={ 'rows': 5 }), required=False)
    highlights = forms.CharField(widget=forms.HiddenInput)
