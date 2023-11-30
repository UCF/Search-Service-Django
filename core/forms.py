from django import forms

from core.widgets import Wysiwyg
from programs.models import Program, ProgramDescription

class CommunicatorProgramForm(forms.Form):
    custom_description = forms.CharField(widget=Wysiwyg())

