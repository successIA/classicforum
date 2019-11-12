from datetime import timedelta
from math import ceil
import random
import string

from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from django.db.models import Max, Min, Count, F, Value, CharField, Prefetch
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from forum.comments.models import Comment
from forum.comments.forms import CommentForm
from forum.threads.models import Thread, ThreadFollowership, ThreadRevision
from forum.categories.models import Category
from forum.core.utils import get_paginated_queryset
from forum.core.constants import COMMENT_PER_PAGE


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


def create_thread_slug(thread, new_slug=None):
    slug = None
    if thread.slug:
        slug = slugify(thread.slug)
    if new_slug:
        slug = new_slug
    else:
        slug = slugify(thread.title)
    qs = Thread.objects.filter(slug=slug)
    if qs.exists():
        s = ''.join(
            [random.choice(string.ascii_lowercase + string.digits)
             for i in range(10)]
        )
        s = s.lower()
        new_slug = '%s-%s' % (slug, s)
        return create_thread_slug(thread, new_slug=new_slug)
    return slug


def get_additional_thread_detail_ctx(request, thread, form_action):
    category = thread.category
    comment_paginator = get_comment_paginator(request, thread)
    if not form_action:
        form_action = thread.get_comment_create_url2(comment_paginator.number)
    first_page = True if comment_paginator.number == 1 else False
    url, count = get_new_comment_info(request.user, request.session, thread)
    ctx = {
        'category': category,
        'comments': comment_paginator,
        'form_action': form_action,
        'first_page': first_page,
        'new_comment_url': url,
        'new_comment_count': count
    }
    return ctx


def get_comment_paginator(request, thread):
    comment_qs = Comment.objects.get_for_thread(thread)
    page_num = request.GET.get('page')
    return get_paginated_queryset(comment_qs, COMMENT_PER_PAGE, page_num)


def update_thread_open_time(session, thread):
    key = '%s_thread_detail_time' % str(thread.slug)
    session[key] = str(timezone.now())


def get_new_comment_info(user, session, thread):
    if not user.is_authenticated:
        return None, None
    if not has_just_commented(session, thread):
        return None, None
    time = get_thread_open_time(session, thread)
    comment_qs = Comment.objects.get_new_for_user(user, thread, time)
    comment = comment_qs.first()
    count = comment_qs.count()
    if comment:
        return comment.get_precise_url(), count
    return comment, count


def has_just_commented(session, thread):
    key = '%s_just_commented' % str(thread.slug)
    just_commented = session.get(key)
    if just_commented:
        del session[key]
    return just_commented


def get_thread_open_time(session, thread):
    key = '%s_thread_detail_time' % str(thread.slug)
    comment_time = session.get(key)
    try:
        comment_time = parse_datetime(comment_time)
    except TypeError:
        comment_time = timezone.now()
    return comment_time


def update_threadfollowership(user, thread, comment_paginator):
    if not user.is_authenticated:
        return
    threadfship = ThreadFollowership.objects.filter(
        user=user,
        thread=thread
    ).first()
    if not threadfship:
        return
    comment_time = threadfship.comment_time
    last_comment, tf_time, unread_count = get_last_comment(
        comment_paginator, comment_time, thread
    )
    unread_count2 = threadfship.new_comment_count
    print('comment_time: ', comment_time)
    # print('last_comment.created: ', last_comment.created)
    print('unread_count: ', unread_count)
    print('unread_count2: ', unread_count2)
    if (unread_count2 - unread_count) < 0:
        unread_count = threadfship.new_comment_count
    if unread_count2 > 0 and unread_count == 0 and not last_comment:
        threadfship.new_comment_count = 0
        threadfship.save()
        return
    if unread_count > 0 and last_comment and tf_time:
        threadfship.comment_time = tf_time
        threadfship.final_comment = last_comment
        threadfship.new_comment_count = F('new_comment_count') - unread_count
        threadfship.save()
        threadfship.refresh_from_db()
        if threadfship.new_comment_count == 0:
            threadfship.has_new_comment = False
            threadfship.save()


def get_last_comment(comment_paginator, comment_time, thread):
    ''' Queryset filter don't work on evaluted_qs '''
    eval_comment_qs = comment_paginator.object_list
    comment_list = [c for c in eval_comment_qs if c.created > comment_time]
    unread_count = len(comment_list)
    last_comment = None
    time = None
    if unread_count > 0:
        last_comment = comment_list[-1]
        time = last_comment.created
    if unread_count > 0 and comment_paginator.has_next():
        page_num = comment_paginator.next_page_number()
        comment_qs = Comment.objects.get_for_thread(thread)
        comment_paginator = get_paginated_queryset(comment_qs, 5, page_num)
        comment = list(comment_paginator.object_list)[0]
        last_comment = comment
        time2 = comment.created
        time = get_average_time(time, time2)
    return last_comment, time, unread_count


def get_average_time(time1, time2):
    if time2 > time1:
        microseconds = (time2 - time1).microseconds / 2
        return time1 + timedelta(microseconds=microseconds)
    return time2
