from django import forms

from core.widgets import Wysiwyg

class CommunicatorProgramForm(forms.Form):
    custom_description = forms.CharField(widget=Wysiwyg(), required=False)
    jobs = forms.CharField()

