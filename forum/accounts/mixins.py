from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model

User = get_user_model()


def profile_owner_required(function):
    def wrap(request, *args, **kwargs):
        if request.user.username != kwargs.get('username'):
            raise PermissionDenied
        return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
