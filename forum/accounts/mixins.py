from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from forum.accounts.models import UserProfile
from django.shortcuts import get_object_or_404, render, redirect
from django.core.exceptions import PermissionDenied
from django.http import Http404


class AccountOwnerMixin(object):

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        username = kwargs.get('username')
        userprofile = get_object_or_404(UserProfile, user__username=username)
        kwargs['userprofile'] = userprofile
        if userprofile.is_owner(request.user):
            return super(AccountOwnerMixin, self).dispatch(request, *args, **kwargs)
        else:
            raise Http404

class ProfileOwnerMixin(object):

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if request.user.username != kwargs.get('username'):
            raise Http404
        return super(ProfileOwnerMixin, self).dispatch(request, *args, **kwargs)

def profile_owner_required(function):
    def wrap(request, *args, **kwargs):
        user = request.user
        if user.username != kwargs.get('username'):
            raise PermissionDenied
        kwargs['userprofile'] = user.userprofile
        return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
