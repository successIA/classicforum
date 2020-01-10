import datetime
import re

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.db import connection, transaction
from django.conf import settings

from forum.core.utils import get_paginated_queryset
from forum.threads.models import (
    Thread, ThreadFollowership
)
from forum.threads.utils import (
    get_filtered_threads,
    get_additional_thread_detail_ctx,
    add_thread_pagination_url_ctx,
    perform_thread_post_update_actions,
    perform_thread_post_create_actions,
)
from forum.comments.utils import (
    perform_comment_save,
    create_comment_revision,
)
from forum.comments.models import Comment, CommentRevision
from forum.categories.models import Category
from forum.threads.models import Thread, ThreadRevision
from forum.categories.views import category_detail
from forum.comments.forms import CommentForm
from forum.moderation.utils import can_view_hidden_posts
from forum.threads.forms import ThreadForm
from forum.threads.mixins import thread_adder, thread_owner_required
from forum.core.constants import THREAD_PER_PAGE, UNSEEN_THREAD_QUERYSTR
from forum.core.utils import get_post_login_redirect_url


def thread_list(request, filter_str=None, page=1, form=None):
    thread_qs = Thread.objects.active()
    unseen_querystring = False
    if can_view_hidden_posts(request):
        thread_qs = Thread.objects.filter()
        unseen_querystring = True
    thread_data = get_filtered_threads(request, filter_str, thread_qs)
    thread_paginator = get_paginated_queryset(
        thread_data[1], THREAD_PER_PAGE, page
    )
    form_action = reverse(
        'threads:thread_create',
        kwargs={'filter_str': thread_data[0], 'page': page}
    )
    home_url = Thread.get_precise_url(thread_data[0], page)
    
    context = {
        'threads': thread_paginator,
        'unseen_querystring': unseen_querystring,
        'show_floating_btn': True,
        'scroll_or_login': get_post_login_redirect_url(home_url),
        'threads_url': "/threads/%s" % (thread_data[0]),
        'form': ThreadForm if not form else form,
        'form_action': form_action + '#comment-form',
        'dropdown_active_text': thread_data[0]
    }
    if unseen_querystring:
        add_thread_pagination_url_ctx(
            context, Thread, thread_paginator, 
            filterstring=thread_data[0], querystr=f"?{UNSEEN_THREAD_QUERYSTR}"    
        )
    else:
        add_thread_pagination_url_ctx(
            context, Thread, thread_paginator, filterstring=thread_data[0]
        )
    return render(request, 'home.html', context)


@login_required
def create_thread(request, slug=None, filter_str=None, page=None):
    form = ThreadForm
    if request.method == 'POST':
        form = ThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.user = request.user
            thread.category = form.cleaned_data.get('category')
            with transaction.atomic():
                thread.save()          
                comment = Comment(
                    message=form.cleaned_data.get('message'),
                    category=form.cleaned_data.get('category'),
                    thread=thread,
                    user=thread.user,
                    is_starting_comment=True
                )
                perform_comment_save(comment)
                thread.set_starting_comment(comment)
                perform_thread_post_create_actions(thread)
            return redirect(thread.get_absolute_url())

    category_list = list(Category.objects.filter(slug=slug))
    if category_list:
        category = category_list[0]
        if request.method == 'GET':
            form = ThreadForm(initial={'category': category})
        return category_detail(request, category.slug, filter_str, page, form)
    else:
        return thread_list(request, filter_str, page, form)


@thread_adder
def thread_detail(
    request, thread_slug, thread=None, form=None, form_action=None
):
    # thread = get_object_or_404(Thread, slug=thread_slug)
    ctx = {
        'thread': thread,
        'starting_comment': thread.starting_comment,
        'form': form if form else CommentForm,
    }
    
    ctx.update(get_additional_thread_detail_ctx(request, thread, form_action))

    comments = ctx['comments']
    thread_fship = None
    count = 0
    if request.user.is_authenticated:
        thread_fship, count = ThreadFollowership.objects.get_instance_and_count(
            thread, user=request.user
        )

        if thread_fship and thread_fship.first_new_comment:
            if comments[-1].created >= thread_fship.first_new_comment.created:
                thread_fship.update_comment_fields(comments)

        ctx.update({'is_thread_follower': True if thread_fship else False})
    else:
        thread_fship, count = ThreadFollowership.objects.get_instance_and_count(
            thread, user=None
        )

    ctx.update({'thread_followers_count': count})
    return render(request, 'threads/thread_detail.html', ctx)


@login_required
@thread_adder
@thread_owner_required
def update_thread(request, thread_slug, thread=None):
    message = thread.starting_comment.message
    form = ThreadForm(instance=thread, initial={'message': message})
    if request.method == 'POST':
        form = ThreadForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                comment = thread.starting_comment
                prev_msg = comment.message
                
                ThreadRevision.objects.create(
                    thread=thread, starting_comment=comment,
                    title=thread.title, message=comment.message,
                    marked_message=comment.marked_message
                )
                create_comment_revision(comment)

                thread.title = form.cleaned_data.get('title')
                thread.message = form.cleaned_data.get('message')
                thread.save()                
                comment.message = form.cleaned_data.get('message')
                perform_comment_save(comment, prev_msg) 
                perform_thread_post_update_actions(thread)           
            return HttpResponseRedirect(thread.get_absolute_url())

    form_action = thread.get_thread_update_form_action()
    return thread_detail(
        request, thread_slug, 
        thread=thread, form=form, form_action=form_action
    )


@login_required
@thread_adder
def follow_thread(request, thread_slug, thread=None):
    # thread = get_object_or_404(Thread, slug=thread_slug)
    ThreadFollowership.objects.toggle(request.user, thread)
    followers_count = thread.followers.count()
    if request.is_ajax():
        return JsonResponse({'followers_count':followers_count})
    return redirect(thread.get_absolute_url())
