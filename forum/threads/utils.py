from django.http import Http404

from forum.accounts.utils import get_user_list_without_creator
from forum.comments.models import Comment
from forum.core.constants import COMMENT_PER_PAGE
from forum.core.utils import (
    add_pagination_context,
    append_querystring,
    get_paginated_queryset,
    get_post_login_redirect_url,
)
from forum.notifications.models import Notification
from forum.threads.models import ThreadFollowership


def get_filtered_threads_for_page(
    request, filter_str=None, thread_qs=None, user=None
):  
    if not request.user.is_authenticated and filter_str == 'me':
        raise Http404
    return _get_filtered_threads(request, filter_str, thread_qs, user)


def get_filtered_threads_for_profile(
    request, filter_str=None, thread_qs=None, user=None
):    
    return _get_filtered_threads(request, filter_str, thread_qs, user)


def _get_filtered_threads(
    request, filter_str=None, thread_qs=None, user=None
):
    auth_filter_list = ['following', 'new']
    if filter_str in auth_filter_list and not request.user.is_authenticated:
        raise Http404

    if filter_str == 'trending':
        return ['trending', thread_qs.get_by_days_from_now(request, days=7)]
    elif filter_str == 'popular':
        return ['popular', thread_qs.get_by_days_from_now(request, days=None)]
    elif filter_str == 'fresh':
        return ['fresh', thread_qs.get_with_no_reply()]
    elif filter_str == 'new':
        return ['new', thread_qs.get_new_for_user(request)]
    elif filter_str == 'following':
        return ['following', thread_qs.get_following_for_user(request)]
    elif filter_str == 'me':
        return ['me', thread_qs.get_recent_for_user(request, user, count=None)]
    
    return ['recent', thread_qs.get_recent(request)]


def get_additional_thread_detail_ctx(request, thread, form_action):
    category = thread.category
    comment_paginator = get_comment_paginator(
        request, thread
    )
    if not form_action:
        form_action = thread.get_comment_create_form_action(
            comment_paginator.number
        )
    first_page = True if comment_paginator.number == 1 else False
    thread_url = f'{thread.get_absolute_url()}?page={comment_paginator.number}'
    base_url = [f'{thread.get_absolute_url()}?page=', '']
    ctx = {
        'category': category,
        'comments': comment_paginator,
        'base_url': base_url,
        'login_redirect_url': get_post_login_redirect_url(thread_url),
        'show_floating_btn': True,
        'form_action': form_action,
        'first_page': first_page
    }
    add_pagination_context(base_url, ctx, comment_paginator)
    return ctx


def get_comment_paginator(request, thread):
    comment_qs = Comment.objects.get_for_thread(thread)    
    page_num = request.GET.get('page')
    return get_paginated_queryset(
        comment_qs, COMMENT_PER_PAGE, page_num
    )

def perform_thread_post_create_actions(thread):
    ThreadFollowership.objects.get_or_create(
        user=thread.user, thread=thread
    )
    notif = Notification(
        sender=thread.user, 
        thread=thread, 
        notif_type=Notification.THREAD_CREATED
    )
    Notification.objects.notify_users(
        notif, thread.user.followers.all()
    )


def perform_thread_post_update_actions(thread):
    followers = get_user_list_without_creator(
        thread.followers.all(), thread.user
    )

    notif = Notification(
        sender=thread.user, 
        thread=thread, 
        notif_type=Notification.THREAD_UPDATED
    )
    Notification.objects.notify_users(
        notif, followers
    )
