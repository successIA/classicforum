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
# def comment_owner_required(function):
#     def wrap(request, *args, **kwargs):
#         comment = get_object_or_404(Comment, pk=kwargs.get('pk'))
#         if comment.is_starting_comment:
#             raise Http404
#         if not comment.is_owner(request.user):
#             raise PermissionDenied
#         kwargs['comment'] = comment
#         return function(request, *args, **kwargs)
#     wrap.__doc__ = function.__doc__
#     wrap.__name__ = function.__name__
#     return wrap


# def vote_perm_required(function):
#     def wrap(request, *args, **kwargs):
#         comment = get_object_or_404(Comment, pk=kwargs.get('pk'))
#         if request.user == comment.user:
#             raise PermissionDenied
#         kwargs['comment'] = comment
#         return function(request, *args, **kwargs)
#     wrap.__doc__ = function.__doc__
#     wrap.__name__ = function.__name__
#     return wrap
