from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm


User = get_user_model()


class UserPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(UserPasswordChangeForm, self).__init__(*args, **kwargs)
        self.fields['new_password1'].help_text = None


class UserSignUpForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254, required=True, widget=forms.EmailInput()
    )
    email2 = forms.EmailField(
        max_length=254, required=True, widget=forms.EmailInput(), label='Confirm Email'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'email2', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(UserSignUpForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = None
        self.fields['password1'].help_text = None

    def clean_email(self):
        email = self.cleaned_data.get('email')
        email_qs = User.objects.filter(email=email)
        if email_qs.exists():
            raise forms.ValidationError(
                'This email has already been registered')
        return email

    def clean_email2(self):
        email = self.cleaned_data.get('email')
        email2 = self.cleaned_data.get('email2')
        if email and email2 and email != email2:
            raise forms.ValidationError('Emails must match.')
        return email


class UserProfileForm(forms.ModelForm):
    image = forms.ImageField(
        widget=forms.ClearableFileInput(), label='', required=False)

    class Meta:
        model = User
        fields = ['image', 'gender', 'signature', 'location', 'website']
        widgets = {
            'signature': forms.Textarea(attrs={'rows': 3})
        }

    def clean_image(self):
        image = self.cleaned_data['image']
        if not image:
            return image
        limit = 2048 * 1024  # 2 MegaBytes 2048 KiloBytes 2097152 Bytes
        if image.size > limit:
            raise forms.ValidationError(
                'File too large. Size should not exceed 500 KB.'
            )
        return image

    # def clean(self):
    #     if not self.cleaned_data.get('image'):
    #         # print('form: ', self)
    #         raise forms.ValidationError(
    #             'Invalid picture or no picture selected. Choose another picture.'
    #         )
