from django import forms

from core.widgets import Wysiwyg

class JobsField(forms.MultipleHiddenInput):
    pass

class CommunicatorProgramForm(forms.Form):
    custom_description = forms.CharField(widget=Wysiwyg(), required=False)
    jobs = forms.CharField()

