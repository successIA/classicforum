import datetime
import re

from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import (
    HttpResponse, HttpResponseRedirect, Http404, HttpResponseForbidden
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views import View
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, FormMixin, UpdateView

from forum.core.utils import get_paginated_queryset
from forum.threads.models import Thread, ThreadFollowership
from forum.threads.utils import (
    get_filtered_threads,
    get_additional_thread_detail_ctx,
    update_threadfollowership,
    update_thread_open_time
)
from forum.comments.models import Comment
from forum.categories.models import Category
from forum.categories.views import category_detail
from forum.comments.forms import CommentForm
from forum.threads.forms import ThreadForm
from forum.threads.mixins import ThreadOwnerMixin, thread_owner_required
from forum.core.constants import THREAD_PER_PAGE


# def thread_list(request, filter_str=None, page=1):
#     form = ThreadForm(request.POST or None)
#     if form.is_valid():
#         if not request.user.is_authenticated:
#             raise PermissionDenied
#         return thread_create(request, form)
#     thread_data = get_filtered_threads(request, filter_str)
#     thread_paginator = get_paginated_queryset(
#         thread_data[1], THREAD_PER_PAGE, page
#     )
#     form_action = reverse(
#         'threads:thread_list_filter',
#         kwargs={'filter_str': thread_data[0], 'page': page}
#     )
#     context = {
#         'threads': thread_paginator,
#         'threads_url': "threads/%s" % (thread_data[0]),
#         'form': form,
#         'form_action': form_action + '#comment-form',
#         'dropdown_active_text': thread_data[0]
#     }
#     return render(request, 'categories/home.html', context)


# @login_required
# def create_thread(request, form):
#     if request.method == 'POST' and form.is_valid():
#         thread = create_thread(form, request.user)
#         return redirect(thread.get_absolute_url())
#     else:
#         raise PermissionDenied


def thread_list(request, filter_str=None, page=1, form=None):
    thread_qs = Thread.objects.active()
    thread_data = get_filtered_threads(request, filter_str, thread_qs)
    thread_paginator = get_paginated_queryset(
        thread_data[1], THREAD_PER_PAGE, page
    )
    form_action = reverse(
        'threads:thread_create',
        kwargs={'filter_str': thread_data[0], 'page': page}
    )
    context = {
        'threads': thread_paginator,
        'threads_url': "/threads/%s" % (thread_data[0]),
        'form': ThreadForm if not form else form,
        'form_action': form_action + '#comment-form',
        'dropdown_active_text': thread_data[0]
    }
    # return render(request, 'categories/home.html', context)
    return render(request, 'home.html', context)


def create_thread(request, slug=None, filter_str=None, page=None):
    if request.method == 'GET':
        raise PermissionDenied
    form = ThreadForm(request.POST or None)
    if form.is_valid():
        thread = form.save(commit=False)
        thread.user = request.user
        thread.category = form.cleaned_data.get('category')
        thread.save()
        comment, created = Comment.objects.get_or_create(
            message=form.cleaned_data.get('message'),
            thread=thread,
            user=request.user,
            is_starting_comment=True
        )

        thread.starting_comment = comment
        thread.save()
        return redirect(thread.get_absolute_url())
    else:
        category_qs = Category.objects.filter(slug=slug)
        if category_qs.count() > 0:
            slug = category_qs.first().slug
            return category_detail(request, slug, filter_str, page, form)
        else:
            return thread_list(request, filter_str, page, form)


def thread_detail(request, thread_slug, form=None, form_action=None):
    thread = get_object_or_404(Thread, slug=thread_slug)
    ctx = {
        'thread': thread,
        'form': form if form else CommentForm,
    }
    ctx.update(get_additional_thread_detail_ctx(request, thread, form_action))

    # comment_pk_list = [comment.pk for comment in ctx['comments']]
    # print("COMMENT_PK_LIST", comment_pk_list)
    # url, count = get_unread_url_and_count(request.user, thread)
    # if request.user.is_authenticated:
    #     CommentActivity.objects.mark_as_read(
    #         request.user, thread, comment_id_list, url
    #     )
    update_threadfollowership(request.user, thread, ctx['comments'])
    update_thread_open_time(request.session, thread)
    return render(request, 'threads/thread_detail.html', ctx)


@login_required
@thread_owner_required
def update_thread(request, thread_slug, thread=None):
    message = thread.starting_comment.message
    form = ThreadForm(instance=thread, initial={'message': message})
    if request.method == 'POST':
        form = ThreadForm(request.POST)
        if form.is_valid():
            comment = thread.starting_comment
            comment.message = form.cleaned_data.get('message')
            comment.save()
            thread.title = form.cleaned_data.get('title')
            thread.message = form.cleaned_data.get('message')
            thread.save()
            return HttpResponseRedirect(thread.get_absolute_url())
    form_action = thread.get_thread_update_url()
    return thread_detail(
        request, thread_slug, form=form, form_action=form_action
    )


@login_required
def follow_thread(request, thread_slug):
    thread = get_object_or_404(Thread, slug=thread_slug)
    thread_key = str(thread.slug) + '_thread_detail_time'
    open_time = request.session.get(thread_key, None)
    if open_time:
        open_time = parse_datetime(open_time)
    if open_time:
        # Use the opening time of the thread so as to allow the user to
        # to get notified of newly added comments if the user stayed on
        # the thread page for some time before clicking on follow btn.
        # toggle_thread_followership(user, thread, open_time)
        ThreadFollowership.objects.toggle_thread_followership(
            request.user, thread, open_time
        )

    else:
        # toggle_thread_followership(user, thread, timezone.now())
        ThreadFollowership.objects.toggle_thread_followership(
            user, thread, open_time
        )
    return redirect(thread.get_absolute_url())
