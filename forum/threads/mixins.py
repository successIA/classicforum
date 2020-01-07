from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

from forum.threads.models import Thread


def thread_adder(function):
    def wrap(request, *args, **kwargs):
        if not kwargs.get("thread"):
            # if (
            #     request.user.is_moderator and 
            #     request.user.moderator.is_moderating_post(thread) and 
            #     kwargs.get("hidden")
            # ):
            #     thread = get_object_or_404(
            #         Thread, slug=kwargs.get("thread_slug")
            #     )
            # else:
            thread = get_object_or_404(
                Thread, visible=True, slug=kwargs.get("thread_slug")
            )
            kwargs['thread'] = thread
        else:
            kwargs["thread"] = kwargs.get("thread")
        return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def thread_owner_required(function):
    def wrap(request, *args, **kwargs):
        # thread = get_object_or_404(Thread, slug=kwargs.get('thread_slug'))
        if not kwargs["thread"].is_owner(request.user):
            raise PermissionDenied
        # kwargs['thread'] = thread
        return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
