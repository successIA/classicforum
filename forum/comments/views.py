import re
from markdown import markdown
from math import ceil

from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import DetailView, ListView
from django.views import View
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.html import mark_safe
from django.utils.decorators import method_decorator

from forum.comments.utils import (
    save_comment,
    set_just_commented,
    get_comment_reply_form
)
from forum.threads.models import Thread
from forum.comments.models import Comment
from forum.comments.forms import CommentForm
from forum.comments.mixins import (
    comment_owner_required,
    vote_perm_required
)    
from forum.threads.views import thread_detail


@login_required
def create_comment(request, thread_slug):
    thread = get_object_or_404(Thread, slug=thread_slug)
    form = CommentForm(request.POST, extra='edit-message')  
    if request.method == 'POST':
        if form.is_valid():
            form.instance.user = request.user
            form.instance.thread = thread
            comment = form.save(commit=False)
            comment = save_comment(comment)
            set_just_commented(request, comment)
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
            comment = form.save(commit=False)
            comment = save_comment(comment)
            return HttpResponseRedirect(comment.get_precise_url())
    form_action = comment.get_update_form_action()
    kwargs = {'form': form, 'form_action': form_action}           
    return thread_detail(request, thread_slug, **kwargs);


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
            comment = form.save(commit=False)
            comment = save_comment(comment)
            return HttpResponseRedirect(comment.get_precise_url())
    form_action = parent_comment.get_reply_form_action()
    kwargs = {'form': form, 'form_action': form_action}           
    return thread_detail(request, thread_slug, **kwargs);


@login_required
@vote_perm_required
def upvote_comment(request, comment=None):
    comment.upvote(request.user)
    return HttpResponseRedirect(comment.get_precise_url())


@login_required
@vote_perm_required
def downvote_comment(request, comment=None):
    comment.downvote(request.user)
    return HttpResponseRedirect(comment.get_precise_url())


@login_required 
def report_comment(request, pk):
    pass