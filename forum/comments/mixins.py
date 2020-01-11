from django.shortcuts import get_object_or_404
from django.http import Http404
from django.core.exceptions import PermissionDenied

from forum.moderation.utils import can_see_post_or_404
from forum.comments.models import Comment
from forum.threads.mixins import thread_adder
from forum.threads.models import Thread

def comment_adder(function):
    @thread_adder
    def wrap(request, *args, **kwargs):
        # all the views using comment_adder do not have a kwarg parma
        # for thread
        del kwargs["thread"]
        comment = get_object_or_404(Comment, pk=kwargs.get("pk"))
        kwargs['comment'] = can_see_post_or_404(request, comment)
        return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def comment_owner_required(function):
    def wrap(request, *args, **kwargs):
        if kwargs["comment"].is_starting_comment:
            raise Http404
        if not kwargs["comment"].is_owner(request.user):
            raise PermissionDenied
        return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def vote_perm_required(function):
    def wrap(request, *args, **kwargs):
        if request.user == kwargs["comment"].user:
            raise PermissionDenied
        return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
