from django.contrib.admin.views.decorators import (
    staff_member_required as _staff_member_required,
    user_passes_test,
)
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model

from .models import Moderator
from ..comments.models import Comment
from ..threads.models import Thread

User = get_user_model()


def staff_member_required(f):
    return _staff_member_required(f, login_url="accounts:login")


def moderator_required(f):
    def wrap(request, *args, **kwargs):
        if request.user.is_moderator:
            return f(request, *args, **kwargs)
        else:
            raise PermissionDenied        
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def supermoderator_or_moderator_owner_required(f):
    @moderator_required
    def wrap(request, *args, **kwargs):
        mod_profile = get_object_or_404(
            Moderator, user__username=kwargs["username"]
        )
        if (
            request.user.moderator.is_supermoderator_to(mod_profile) or
            mod_profile.is_owner(request.user.moderator)
        ):
            kwargs["mod_profile"] = mod_profile
            return f(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def _set_post_moderation_kwargs(request, kwargs):
    post_key = None
    if kwargs.get("slug"):
        _set_thread_moderation_kwargs(request, kwargs)
        post_key = "thread"
    elif kwargs.get("comment_pk"):
        _set_comment_moderation_kwargs(request, kwargs)
        post_key = "comment"
    kwargs["mod"] = request.user.moderator
    return post_key


def _set_thread_moderation_kwargs(request, kwargs):
    kwargs["thread"] = get_object_or_404(Thread, slug=kwargs.get("slug"))


def _set_comment_moderation_kwargs(request, kwargs):
    kwargs["comment"] = get_object_or_404(Comment, pk=kwargs.get("comment_pk"))


def post_moderator_required(f):
    @moderator_required
    def wrap(request, *args, **kwargs):
        post_key = _set_post_moderation_kwargs(request, kwargs)
        if not kwargs["mod"].is_moderating_post(kwargs[post_key]):
            raise PermissionDenied
        return f(request, *args, **kwargs)
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def hide_post_permission_required(f):
    @moderator_required
    def wrap(request, *args, **kwargs):
        post_key = _set_post_moderation_kwargs(request, kwargs)
        if kwargs["mod"].can_hide_post(kwargs[post_key]):
            return f(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def unhide_post_permission_required(f):
    @moderator_required
    def wrap(request, *args, **kwargs):
        post_key = _set_post_moderation_kwargs(request, kwargs)
        if kwargs["mod"].can_unhide_post(kwargs[post_key]):
            return f(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap

