from django import forms
from django.forms import ModelForm
from django.core.exceptions import ValidationError

from forum.attachments.models import Attachment

def file_size(value): # add this to some file where you can import it from
    limit = 500 * 1024 
    print(value.size)
    if value.size > limit:
        raise forms.ValidationError(
            'File too large. Size should not exceed 500 KB.'
        )


class AttachmentForm(ModelForm):
    # image = forms.FileField(required=False, validators=[file_size])

    def __init__(self, *args, **kwargs):
        super(AttachmentForm, self).__init__(*args, **kwargs)
        self.fields['image'].required = True
        # self.fields['image'] = forms.ImageField(validators=[file_size])
        
    class Meta:
        model = Attachment
        fields = ['image']

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            return image
        limit = 2048 * 1024  # 2 MegaBytes 2048 KiloBytes 2097152 Bytes
        if image.size > limit:
            raise forms.ValidationError(
                'File too large. Size should not exceed 500 KB.'
            )
        return image




     


