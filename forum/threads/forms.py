from django.shortcuts import get_object_or_404
from django import forms

from forum.threads.models import Thread


class ThreadForm(forms.ModelForm):

    message = forms.CharField(widget=forms.Textarea)
    # category = forms.CharField(widget=forms.TextInput)

    class Meta:
        model = Thread
        fields = ['category', 'title', 'message', ]

    # def __init__(self, *args, **kwargs):
    #     super(ThreadForm2, self).__init__(*args, **kwargs)
    #     print('self.initial: ', self.initial)
    #     if self.initial.get('category'):
    #         print('BEFORE')
    #     #     from forum.categories.models import Category
    #     #     print('HIIIIHT')
    #     #     self.fields['category'].queryset = Category.objects.all()
    #     # else:
    #         self.fields['category'] = forms.CharField(
    #             widget=forms.TextInput(
    #                 attrs={'readonly':'readonly'}
    #             )
    #         )
    #     self.fields['category'].required = True
    #     self.fields['message'].required = True
    #     self.fields['message'] = forms.CharField(
    #         widget=forms.Textarea(
    #             attrs={'cols': '40', 'rows': '10', 'maxlength': '4000'}
    #         )
    #     )    

    # def clean_message(self):
    #     message = self.cleaned_data['message']
    #     if not message:
    #         raise forms.ValidationError("Message can't be blank")
    #     return message
   