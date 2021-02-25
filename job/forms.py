from django import forms
from django.forms.models import inlineformset_factory
from .models import *

class TalkJobManagementForm(forms.Form):
    dataset_id = forms.CharField(label='')