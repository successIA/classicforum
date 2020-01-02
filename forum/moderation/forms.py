from itertools import chain

from django import forms
from django.forms import models
from django.forms.fields import MultipleChoiceField
from django.contrib.auth import get_user_model

from ..categories.models import Category
from .models import Moderator, ModeratorEvent, ModeratorQuerySet

User = get_user_model()


# customizing the ModelChoiceField made available in Django
# to have a better control at the data being displayed in the template(s)
class AdvancedModelChoiceIterator(models.ModelChoiceIterator):
    def choice(self, obj):
        return (self.field.prepare_value(obj), self.field.label_from_instance(obj), obj)

class AdvancedModelChoiceField(models.ModelMultipleChoiceField):
    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices
        return AdvancedModelChoiceIterator(self)
    choices = property(_get_choices, MultipleChoiceField._set_choices)


class ModeratorForm(forms.Form):
    user = forms.CharField()
    categories = AdvancedModelChoiceField(
        widget = forms.CheckboxSelectMultiple,
        queryset=Category.objects.all(),
        label="The above user will be moderating the categories selected in the"
              " list below. The user will be able to hide threads and comments"
              " within the categories and also ban users when they post"
              " illegal threads or comments under the categories.",
        to_field_name="slug",
        required=True,
        error_messages={
            "required": "You have to select one or more categories." 
        }
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop("instance", None)
        super(ModeratorForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields["user"].required = False


    def clean_user(self):
        username =self.cleaned_data.get("user")        
        user = None
        if not self.instance:            
            if Moderator.objects.filter(user__username=username).exists():
                raise forms.ValidationError("User is already a moderator.")            
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise forms.ValidationError("User does not exist.")
        return user
