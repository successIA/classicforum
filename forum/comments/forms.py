from django import forms
from django.shortcuts import get_object_or_404

from forum.comments.models import Comment


class CommentForm(forms.ModelForm):
    message = forms.CharField(widget=forms.Textarea(
        attrs={'placeholder': 'What are your thoughts?'}), label=''
    )

    class Meta:
        model = Comment
        fields = ['message', ]

    @staticmethod
    def get_for_reply(message):
        return CommentForm(instance=Comment(message=message))
