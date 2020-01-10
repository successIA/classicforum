from django.http import Http404

from forum.accounts.utils import get_user_list_without_creator
from forum.comments.models import Comment
from forum.core.constants import (
    COMMENT_PER_PAGE, 
    UNSEEN_COMMENT_QUERYSTR, 
    UNSEEN_THREAD_QUERYSTR,
)
from forum.core.utils import (
    get_paginated_queryset,
    get_post_login_redirect_url
)
from forum.moderation.utils import is_auth_and_moderator, can_see_post
from forum.notifications.models import Notification
from forum.threads.models import ThreadFollowership


def get_filtered_threads(request, filter_str=None, thread_qs=None):
    RECENT = 'recent'
    # auth_filter_list = ['following', 'new', 'me']
    auth_filter_list = ['following', 'new']
    if filter_str in auth_filter_list and not request.user.is_authenticated:
        raise Http404
    threads_dict = {
        RECENT: thread_qs.get_recent(request.user),
        'trending': thread_qs.get_by_days_from_now(request.user, days=7),
        'popular': thread_qs.get_by_days_from_now(request.user, days=None),
        'fresh': thread_qs.get_with_no_reply(),
        'new': thread_qs.get_new_for_user(request.user),
        'following': thread_qs.get_following_for_user(request.user),
        'me': thread_qs.get_only_for_user(request.user),
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


def get_create_form_action(self, filter_str, page):
    return reverse(
        'threads:thread_list_filter',
        kwargs={'filter_str': filter_str, 'page': page}
    )


def join_with_invisible_threads(request, thread_qs):
    from ..threads.models import Thread

    unseen = request.GET.get("unseen")
    if unseen:
        try:
            unseen = int(unseen)
            if is_auth_and_moderator(request) and unseen == 1:
                return Thread.objects.filter()
        except ValueError:
            pass
    return thread_qs


def get_additional_thread_detail_ctx(request, thread, form_action):
    category = thread.category
    comment_paginator, has_invisible_comments = get_comment_paginator(
        request, thread
    )
    if not form_action:
        form_action = thread.get_comment_create_form_action(
            comment_paginator.number
        )
    first_page = True if comment_paginator.number == 1 else False
    thread_url = f'{thread.get_absolute_url()}?page={comment_paginator.number}'
    ctx = {
        'category': category,
        'comments': comment_paginator,
        'unseen_querystring': has_invisible_comments,
        'scroll_or_login': get_post_login_redirect_url(thread_url),
        'show_floating_btn': True,
        'form_action': form_action,
        'first_page': first_page
    }

    if not thread.visible or has_invisible_comments:
        if not thread.visible and has_invisible_comments:
            querystring = f"&{UNSEEN_THREAD_QUERYSTR}&{UNSEEN_COMMENT_QUERYSTR}"
        elif not thread.visible:
            querystring = f"&{UNSEEN_THREAD_QUERYSTR}"
        elif has_invisible_comments:
            querystring = f"&{UNSEEN_COMMENT_QUERYSTR}"
        add_thread_pagination_url_ctx(
            ctx, thread, comment_paginator, querystr=querystring   
        )
    else:
        add_thread_pagination_url_ctx(
            ctx, thread, comment_paginator
        )
    return ctx


def get_comment_paginator(request, thread):
    comment_qs = Comment.objects.get_for_thread(thread)
    unseen_querystring = False
    # if can_see_post(request, thread):
    if (
        is_auth_and_moderator(request) and 
        request.user.moderator.is_moderating_post(thread) and
        str(request.GET.get("unseen_c")) == "1"
    ):
        comment_qs = _join_comments_visible_to_user(
            request, thread, comment_qs
        )
        unseen_querystring = True
    
    page_num = request.GET.get('page')
    return get_paginated_queryset(
        comment_qs, COMMENT_PER_PAGE, page_num
    ), unseen_querystring


def _join_comments_visible_to_user(request, thread, comment_qs):
    categories = request.user.moderator.categories.all()
    comment_qs = Comment.objects.filter(
        thread=thread, category__in=categories
    ).get_related().union(comment_qs).order_by('created')
    return comment_qs


# {{ threads_url }}/{{ page_obj.previous_page_number }}{% if unseen_query %}?unseen=1{% endif %}/ 
def add_thread_pagination_url_ctx(
    context, model, paginator, filterstring=None, querystr=None
):
    # from ..threads.models import Thread

    if paginator.has_next():
        next_url = model.get_precise_url2(
            model=model, 
            filterstring=filterstring, 
            page=paginator.next_page_number()
        )
        if querystr:
            next_url = f"{next_url}{querystr}"
        context["next_url"] = next_url
    if paginator.has_previous():
        prev_url = model.get_precise_url2(
            model=model, 
            filterstring=filterstring, 
            page=paginator.previous_page_number()
        )
        if querystr:
            prev_url = f"{prev_url}{querystr}"
        context["prev_url"] = prev_url
    


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
