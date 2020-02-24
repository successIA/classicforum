from django.shortcuts import get_object_or_404
from django import forms


from forum.categories.models import Category
from forum.threads.models import Thread


class ThreadForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(), empty_label='Choose a category', label=''
    )
    title = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Title', }),
        label=''
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'What are your thoughts?', }), 
        label=''
    )

    class Meta:
        model = Thread
        fields = ['category', 'title', 'message', ]
        

