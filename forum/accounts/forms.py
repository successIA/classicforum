from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils.datastructures import MultiValueDict

from forum.attachments.forms import AttachmentForm

User = get_user_model()


class UserPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(UserPasswordChangeForm, self).__init__(*args, **kwargs)
        self.fields['new_password1'].help_text = None


class UserSignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=False,
        max_length=254,
        widget=forms.EmailInput(),
        help_text='You may leave this field empty.'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(UserSignUpForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = None
        self.fields['password1'].help_text = None

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                'This username has already been registered'
            )
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return email

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'This email has already been registered'
            )
        return email


class UserProfileForm(forms.ModelForm):
    image = forms.ImageField(
        widget=forms.ClearableFileInput(), label='', required=False
    )

    class Meta:
        model = User
        fields = ['image', 'gender', 'signature', 'location', 'website']
        widgets = {
            'signature': forms.Textarea(attrs={'rows': 3})
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            a_f = AttachmentForm()
            cleaned_data = {'image': image}
            a_f.cleaned_data = cleaned_data
            return a_f.clean_image(size=(300, 300))
        return image
