from django.shortcuts import Http404

from ..comments.models import Comment


def can_see_post_or_404(request, post):
    if not post.visible:
        if can_see_post(request, post):
            return post        
        else: 
            raise Http404
    else:
        if isinstance(post, Comment):
            can_see_post_or_404(request, post.thread)
    return post


def can_see_post(request, post):
    return (
        has_unseen_querystring(request) and
        is_auth_and_moderator(request) and
        request.user.moderator.is_moderating_post(post)
    )      


def can_view_hidden_posts(request):
    return (
        has_unseen_querystring(request) and
        is_auth_and_moderator(request)
    )


def has_unseen_querystring(request):
    unseen = request.GET.get("unseen")
    if unseen:
        try:
            unseen = int(unseen)
            if unseen == 1:                
                return True
        except ValueError:
            pass
    return False


def is_auth_and_moderator(request):
    return (
        request.user.is_authenticated and request.user.is_moderator
    )

