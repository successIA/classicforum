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


def get_filtered_threads(request, filter_str=None, thread_qs=None):
    RECENT = 'recent'
    # auth_filter_list = ['following', 'new', 'me']
    auth_filter_list = ['following', 'new']
    if filter_str in auth_filter_list and not request.user.is_authenticated:
        raise Http404
    threads_dict = {
        RECENT: thread_qs.get_recent(request),
        'trending': thread_qs.get_by_days_from_now(request, days=7),
        'popular': thread_qs.get_by_days_from_now(request, days=None),
        'fresh': thread_qs.get_with_no_reply(),
        'new': thread_qs.get_new_for_user(request),
        'following': thread_qs.get_following_for_user(request),
        'me': thread_qs.get_only_for_user(request),
    }
    all_filter_list = auth_filter_list + ['trending', 'popular', 'fresh']
    # Recent threads are returned for invalid filters as default.
    # However, threads_dict.get(filter_str) may return an empty queryset
    # if there is no thread for the current selection. So also perform check
    # for that situation to avoid getting recent threads for valid filters
    # with no threads
    if filter_str not in list(threads_dict.keys()):
        # print('recent')
        # if not threads_dict.get(filter_str) and filter_str not in all_filter_list:
        return [RECENT, threads_dict[RECENT]]
    return [filter_str, threads_dict[filter_str]]


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
        'scroll_or_login': get_post_login_redirect_url(thread_url),
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
    # TODO A notification should not be sent if thread is invisible
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

    # TODO A notification should not be sent if thread is invisible
    notif = Notification(
        sender=thread.user, 
        thread=thread, 
        notif_type=Notification.THREAD_UPDATED
    )
    Notification.objects.notify_users(
        notif, followers
    )
