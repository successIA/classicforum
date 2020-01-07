from django.shortcuts import get_object_or_404
from django.http import Http404
from django.core.exceptions import PermissionDenied

from forum.comments.models import Comment
from forum.threads.models import Thread


def comment_adder(function):
    def wrap(request, *args, **kwargs):
        comment = Comment.objects.pure_and_thread_active_or_404(
            kwargs.get("pk")
        )
        kwargs['comment'] = comment
        # kwargs["thread"] = comment.thread
        return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def comment_owner_required(function):
    def wrap(request, *args, **kwargs):
        # comment = get_object_or_404(Comment, pk=kwargs.get('pk'))
        if kwargs["comment"].is_starting_comment:
            raise Http404
        if not kwargs["comment"].is_owner(request.user):
            raise PermissionDenied
        # kwargs['comment'] = comment
        return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def vote_perm_required(function):
    def wrap(request, *args, **kwargs):
        # comment = get_object_or_404(Comment, pk=kwargs.get('pk'))
        if request.user == kwargs["comment"].user:
            raise PermissionDenied
        # kwargs['comment'] = comment
        return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
