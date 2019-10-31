import datetime
import re

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

from forum.core import (
    HomePageViewEnum as HOME,
    get_home_page_default_context,
    get_home_page_template
)

from forum.categories import (
    CategoryViewEnum as CATEGORY,
    get_category_default_context,
)

from forum.accounts import (
    UserProfileViewEnum as USER_PROFILE,
    get_userprofile_default_context,
)

from forum.core.utils import get_paginated_queryset
from forum.threads import ThreadViewEnum as THREAD
from forum.threads.models import Thread
from forum.threads.utils import (
    toggle_thread_followership,
    get_additional_thread_detail_context,
    update_threadfollowership,
    update_thread_open_time
)
from forum.comments.models import Comment
from forum.categories.models import Category
from forum.comments.forms import CommentForm
from forum.threads.forms import ThreadForm, ThreadForm2
from forum.utils import save_chosen_images, delete_unticked_images
from forum.image_app.models import Image
from forum.threads import new_thread_utils
from forum.notifications.models import Notification
from forum.accounts.models import UserProfile
from forum.threads.utils import create_thread, filter_threads, update_thread
from forum.threads.mixins import ThreadOwnerMixin



class ThreadListView(View):

    def dispatch(self, request, *args, **kwargs):
        filter_str = kwargs.get('filter')
        thread_qs = Thread.objects.active()

        filtered_threads, valid_filter_str = filter_threads(
            request, thread_qs, filter_str=filter_str
        )

        # thread_qs = thread_qs.get_recent(self.request.user)
        thread_paginator = get_paginated_queryset(
            filtered_threads, 10, kwargs.get('page')
        )

        form = ThreadForm2()
        self.context = {
            'threads': thread_paginator,
            'threads_url': "threads/%s" % (valid_filter_str),
            'form': form,
            'dropdown_active_text': valid_filter_str
        }
        return super(ThreadListView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, 'categories/home.html', self.context)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        form = ThreadForm2(request.POST)
        if form.is_valid():
            view = ThreadCreateView.as_view(form=form);
            return view(request, *args, **kwargs)
        else:
            self.context.update({'form': form})
            return render(request, 'categories/home.html', self.context)


class ThreadCreateView(View):
    form = ''

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        if not self.form:
            raise ValueError("You have to initialize the form instance in in as_view().")
        thread = create_thread(self.form, request.user)
        return HttpResponseRedirect(thread.get_absolute_url())


class ThreadDetailBaseView(View):
    context = ''
    form_obj = ''

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        if kwargs.get('thread'):
            self.thread = kwargs.get('thread')
        else:
            self.thread = get_object_or_404(Thread, slug=kwargs.get('thread_slug')) 
        comment_qs = Comment.objects.get_for_thread(self.thread)
        self.comment_paginator = get_paginated_queryset(
            comment_qs, 5, request.GET.get('page')
        )
        return super(ThreadDetailBaseView, self).dispatch(request, *args, **kwargs)        

    def get(self, request, *args, **kwargs):
        self.add_default_context()
        self.perform_default_action()
        return render(request, 'threads/thread_detail.html', self.context)

    def post(self, request, *args, **kwargs):
        self.add_default_context()
        self.perform_default_action()
        return render(request, 'threads/thread_detail.html', self.context)

    def add_default_context(self):
        form_action = self.thread.get_comment_create_url2(self.comment_paginator.number)
        context = {
            'thread': self.thread,
            'comments': self.comment_paginator,
        }
        if self.form_obj:
            context.update({'form': self.form_obj})
        self.context = get_additional_thread_detail_context(
            self.request.user,
            self.thread,
            context,
            self.request.session,
            self.comment_paginator.number 
        )

    def perform_default_action(self):
        update_threadfollowership(
            self.request.user, self.thread, self.comment_paginator
        )
        update_thread_open_time(self.request.session, self.thread) 


class ThreadDetailView(ThreadDetailBaseView):
    context = ''

    def get(self, request, *args, **kwargs):
        self.form_obj = CommentForm
        return super(ThreadDetailView, self).get(request, *args, **kwargs)        

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        from forum.comments.views import CommentCreateView2

        form = CommentForm(request.POST, extra='edit-message')
        if form.is_valid():
            form.instance.thread = self.thread
            view = CommentCreateView2.as_view(form=form);
            return view(request, *args, **kwargs)
        self.form_obj = form
        return super(ThreadDetailView, self).post(request, *args, **kwargs)        


class ThreadUpdateView(ThreadOwnerMixin, ThreadDetailBaseView):

    def get(self, request, *args, **kwargs):
        message = self.thread.starting_comment.message
        self.form_obj = ThreadForm2(
            instance=self.thread,
            initial={'message': message}
        )
        return super(ThreadUpdateView, self).get(request, *args, **kwargs)        

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        form = ThreadForm2(request.POST)
        if form.is_valid():
            thread = update_thread(form, request.user, self.thread.pk)
            return HttpResponseRedirect(thread.get_absolute_url())
        self.form_obj = form
        return super(ThreadUpdateView, self).post(request, *args, **kwargs)        

    
class ThreadFollowView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        thread_slug = kwargs.get('thread_slug')
        thread = get_object_or_404(Thread, slug=thread_slug)
        userprofile = request.user.userprofile
        thread_key = str(thread.slug) + '_thread_detail_time'
        open_time = self.request.session.get(thread_key, None)
        if open_time:
            open_time = parse_datetime(open_time)
        if open_time:
            # Use the opening time of the thread so as to allow the user to
            # to get notified of newly added comments if the user stayed on
            # the thread page for some time before clicking on follow btn.
            toggle_thread_followership(userprofile, thread, open_time)
        else:
            # print('KETTTTTTTLE')
            toggle_thread_followership(userprofile, thread, timezone.now())
        return redirect(thread.get_absolute_url())
