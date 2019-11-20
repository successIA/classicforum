import re

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator

from forum.comments.forms import CommentForm
from forum.comments.mixins import comment_owner_required, vote_perm_required
from forum.comments.models import Comment
from forum.comments.utils import get_comment_reply_form
from forum.threads.models import Thread
from forum.threads.views import thread_detail


@login_required
def create_comment(request, thread_slug):
    thread = get_object_or_404(Thread, slug=thread_slug)
    form = CommentForm(extra='edit-message')
    if request.method == 'POST':
        form = CommentForm(request.POST, extra='edit-message')
        if form.is_valid():
            form.instance.user = request.user
            form.instance.thread = thread
            comment = form.save()
            return HttpResponseRedirect(comment.get_precise_url())
    return thread_detail(request, thread_slug, form=form)


@login_required
@comment_owner_required
def update_comment(request, thread_slug, pk, comment=None):
    form = CommentForm(instance=comment, extra='edit-message')
    if request.method == 'POST':
        form = CommentForm(
            request.POST, instance=comment, extra='edit-message'
        )
        if form.is_valid():
            form.instance.pk = comment.pk
            form.instance.user = request.user
            form.instance.thread = comment.thread
            comment = form.save()
            return HttpResponseRedirect(comment.get_precise_url())
    form_action = comment.get_update_form_action()
    kwargs = {'form': form, 'form_action': form_action}
    return thread_detail(request, thread_slug, **kwargs)


@login_required
def reply_comment(request, thread_slug, pk):
    parent_comment = get_object_or_404(Comment, pk=pk)
    form = get_comment_reply_form(parent_comment)
    if request.method == 'POST':
        form = CommentForm(request.POST, extra='edit-message')
        if form.is_valid():
            form.instance.parent = parent_comment
            form.instance.user = request.user
            form.instance.thread = parent_comment.thread
            comment = form.save()
            return HttpResponseRedirect(comment.get_precise_url())
    form_action = parent_comment.get_reply_form_action()
    kwargs = {'form': form, 'form_action': form_action}
    return thread_detail(request, thread_slug, **kwargs)


@login_required
@vote_perm_required
def upvote_comment(request, thread_slug=None, pk=None, comment=None):
    comment.upvote(request.user)
    return HttpResponseRedirect(comment.get_precise_url())


@login_required
@vote_perm_required
def downvote_comment(request, thread_slug=None, pk=None, comment=None):
    comment.downvote(request.user)
    return HttpResponseRedirect(comment.get_precise_url())


@login_required
def report_comment(request, pk):
    pass
