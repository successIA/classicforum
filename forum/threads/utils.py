from django.http import Http404

from forum.comments.models import Comment
from forum.core.constants import COMMENT_PER_PAGE
from forum.core.utils import get_paginated_queryset


def get_filtered_threads(request, filter_str=None, thread_qs=None):
    RECENT = 'recent'
    auth_filter_list = ['following', 'new', 'me']
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
    if not threads_dict.get(filter_str) and filter_str not in all_filter_list:
        return [RECENT, threads_dict[RECENT]]
    return [filter_str, threads_dict[filter_str]]


def get_create_form_action(self, filter_str, page):
    return reverse(
        'threads:thread_list_filter',
        kwargs={'filter_str': filter_str, 'page': page}
    )


def get_additional_thread_detail_ctx(request, thread, form_action):
    category = thread.category
    comment_paginator = get_comment_paginator(request, thread)
    if not form_action:
        form_action = thread.get_comment_create_form_action(
            comment_paginator.number
        )
    first_page = True if comment_paginator.number == 1 else False
    ctx = {
        'category': category,
        'comments': comment_paginator,
        'form_action': form_action,
        'first_page': first_page
    }
    return ctx


def get_comment_paginator(request, thread):
    comment_qs = Comment.objects.get_for_thread(thread)
    page_num = request.GET.get('page')
    return get_paginated_queryset(comment_qs, COMMENT_PER_PAGE, page_num)
