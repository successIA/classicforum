from django.core.exceptions import PermissionDenied
from django.shortcuts import Http404

from ..comments.models import Comment


def can_see_post_or_404(request, post):
    if not post.visible:
        if (
            request.user.is_authenticated and
            request.user.is_moderator and
            request.user.moderator.is_moderating_post(post)
        ):
            if request.method == "POST":
                raise PermissionDenied
            return post        
        else: 
            raise Http404
    # else:
    #     if isinstance(post, Comment):
    #         can_see_post_or_404(request, post.thread)
    return post
