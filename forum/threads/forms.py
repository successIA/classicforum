from django.shortcuts import get_object_or_404
from django import forms

from forum.threads.models import Thread


class ThreadForm(forms.ModelForm):
    message = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Thread
        fields = ['category', 'title', 'message', ]
