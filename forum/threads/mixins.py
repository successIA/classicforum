from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

from forum.threads.models import Thread
from forum.moderation.utils import can_see_post_or_404


def thread_adder(function):
    def wrap(request, *args, **kwargs):
        if kwargs.get("thread"):
            can_see_post_or_404(request, kwargs["thread"])            
        else:
            thread = get_object_or_404(
                Thread, slug=kwargs.get("thread_slug")
            )
            kwargs["thread"] = can_see_post_or_404(request, thread)        
        return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def thread_owner_required(function):
    def wrap(request, *args, **kwargs):
        if not kwargs["thread"].is_owner(request.user):
            raise PermissionDenied
        return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
