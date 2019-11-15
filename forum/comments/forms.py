from django.shortcuts import get_object_or_404
from django import forms

from forum.comments.models import Comment


class CommentForm(forms.ModelForm):
    message = forms.CharField(widget=forms.Textarea, label='')

    class Meta:
        model = Comment
        fields = ['message', ]

    def get_for_reply(message, extra=None):
        return CommentForm(instance=Comment(message=message), extra=extra)

    def __init__(self, *args, **kwargs):
        extra = kwargs.pop('extra', 'NA')
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['message'] = forms.CharField(
            widget=forms.Textarea(attrs={'id': extra})
        )
