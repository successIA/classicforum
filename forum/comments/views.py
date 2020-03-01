import re

from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator

from forum.comments.forms import CommentForm
from forum.comments.mixins import (
    comment_owner_required, 
    comment_adder,
)
from forum.comments.models import Comment, CommentRevision
from forum.comments.utils import (
    get_comment_reply_form,
    perform_comment_save,
    create_comment_revision,
)
from forum.notifications.models import Notification
from forum.threads.models import Thread
from forum.threads.views import thread_detail
from forum.threads.mixins import thread_adder


@login_required
@thread_adder
def create_comment(request, thread_slug, thread=None):
    form = CommentForm
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                form.instance.user = request.user
                form.instance.thread = thread
                form.instance.category = thread.category
                comment = form.save(commit=False)
                perform_comment_save(comment) 
            return HttpResponseRedirect(comment.get_precise_url())
    return thread_detail(
        request, thread_slug, form=form, thread=thread
    )


@login_required
@comment_adder
@comment_owner_required
def update_comment(request, thread_slug, pk, comment=None):
    form = CommentForm(instance=comment)
    if request.method == 'POST':
        # message must be backed up here
        prev_msg = comment.message
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():            
            with transaction.atomic():
                form.instance.pk = comment.pk
                form.instance.user = request.user
                form.instance.thread = comment.thread
                # Despite the fact that the comment obj used below has 
                # been updated, the current comment in the db will
                # used for creating a valid revision.
                create_comment_revision(comment)
                comment = form.save(commit=False)
                perform_comment_save(comment, prev_msg)
            return HttpResponseRedirect(comment.get_precise_url())

    form_action = comment.get_update_form_action()
    kwargs = {
        'form': form, 
        'form_action': form_action, 
        'thread': comment.thread
    }
    return thread_detail(request, thread_slug, **kwargs)


@login_required
@comment_adder
def reply_comment(request, thread_slug, pk, comment=None):
    parent_comment = comment
    form = get_comment_reply_form(parent_comment)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                thread = parent_comment.thread
                form.instance.parent = parent_comment
                form.instance.user = request.user
                form.instance.thread = thread
                form.instance.category = thread.category
                comment = form.save(commit=False)
                perform_comment_save(comment)
                if request.user != comment.parent.user:
                    Notification.objects.create(
                        sender=comment.user,
                        receiver=comment.parent.user,
                        comment=comment,
                        notif_type=Notification.COMMENT_REPLIED
                    )
            return HttpResponseRedirect(comment.get_precise_url())

    form_action = parent_comment.get_reply_form_action()
    kwargs = {
        'form': form, 
        'form_action': form_action, 
        'thread': comment.thread
    }
    return thread_detail(request, thread_slug, **kwargs)


@login_required
@comment_adder
def like_comment(request, thread_slug=None, pk=None, comment=None):
    if request.method == 'POST':
        likers_count, is_liker = comment.toggle_like(request.user)
        if request.is_ajax():
            return JsonResponse(
                {
                    'likers_count': likers_count,
                    'is_liker': is_liker               
                }
            )
    return HttpResponseRedirect(comment.get_precise_url())
    

@login_required
def report_comment(request, pk):
    pass
