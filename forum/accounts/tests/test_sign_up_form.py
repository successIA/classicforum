from django.test import TestCase

from forum.accounts.forms import UserSignUpForm


class SignUpFormTest(TestCase):
    def test_form_has_fields(self):
        form = UserSignUpForm()
        expected = ['username', 'email', 'password1', 'password2', ]
        actual = list(form.fields)
        self.assertSequenceEqual(expected, actual)
