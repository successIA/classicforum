import json

from django.contrib.auth import login as auth_login
from django.core.urlresolvers import reverse_lazy, reverse
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView
from django.contrib.auth.models import User
from django.views import View
from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import Http404
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth.views import PasswordChangeDoneView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Max, Min, Count, F, Value, CharField, Prefetch, Sum
from django.http import JsonResponse

from forum.accounts.tokens import account_activation_token
from forum.accounts.models import UserProfile
from forum.accounts.forms import UserProfileForm
from forum.accounts.forms import UserSignUpForm
from forum.threads.utils import get_filtered_threads
from forum.threads.models import ThreadFollowership, Thread
from forum.notifications.models import Notification
from forum.comments.models import Comment
from forum.core.utils import get_paginated_queryset
from forum.accounts.mixins import profile_owner_required
from forum.accounts.utils import (
    get_mentioned_users_context,
    get_signup_email_confirm_form_entries
)


def user_profile_stats(request, username):
    userprofile = get_object_or_404(UserProfile, user__username=username)
    user = userprofile.user
    ctx = {
        'userprofile': userprofile,
        'dropdown_active_text2': 'stats',
        'last_posted': Comment.objects.get_user_last_posted(user),
        'active_category': Comment.objects.get_user_active_category(user),
        'total_upvotes': Comment.objects.get_user_total_upvotes(user),
        'total_upvoted': Comment.objects.filter(upvoters=user).count(),
        'recent_comments': Comment.objects.get_recent_for_user(user, 5),
        'recent_threads': Thread.objects.get_recent_for_user(request, user)
    }
    return render(request, 'accounts/profile_stats.html', ctx)


@login_required
@profile_owner_required
def user_notification_list(request, username, userprofile):
    notifs = Notification.objects.get_for_user(username)
    ctx = {
        'userprofile': userprofile,
        'dropdown_active_text2': 'user_notifs',
        'notifications': notifs
    }
    return render(request, 'accounts/profile_notif.html', ctx)


@login_required
@profile_owner_required
def user_profile_edit(request, username, userprofile):
    form = UserProfileForm(instance=userprofile)
    if request.method == 'POST':
        form = UserProfileForm(
            request.POST, request.FILES, instance=userprofile)
        if form.is_valid():
            image = form.cleaned_data.get('image')
            from forum.attachments.models import Attachment
            Attachment.objects.create_with_userprofile(image, userprofile)
            form.save()
            messages.success(request, 'Profile updated successfully!')
            username = userprofile.user.username
            return HttpResponseRedirect(
                reverse('accounts:user_edit', kwargs={'username': username})
            )
    ctx = {
        'userprofile': userprofile,
        'dropdown_active_text2': 'profile',
        'form': form
    }
    return render(request, 'accounts/profile_info.html', ctx)


def user_comment_list(request, username, page):
    user = User.objects.filter(username=username).first()
    comment_qs = Comment.objects.filter(user=user).exclude(
        is_starting_comment=True
    ).get_related().order_by('id')
    comments = get_paginated_queryset(comment_qs, 10, page)
    ctx = {
        'comments': comments,
        'dropdown_active_text2': 'replies',
        'userprofile': user.userprofile
    }
    return render(request, 'accounts/profile_comments.html', ctx)


def user_thread_list(request, username, filter_str, page):
    userprofile = get_object_or_404(
        UserProfile, user__username=username
    )
    if not userprofile.is_required_filter_owner(request.user, filter_str):
        raise Http404
    user = userprofile.user
    thread_qs = Thread.objects.active()
    thread_data = get_filtered_threads(request, filter_str, thread_qs)
    thread_paginator = get_paginated_queryset(thread_data[1], 10, page)
    ctx = {
        'userprofile': userprofile,
        'threads': thread_paginator,
        'threads_url': '/accounts/%s/%s' % (username, thread_data[0]),
        'dropdown_active_text2': thread_data[0]
    }
    return render(request, 'accounts/profile_threads.html', ctx)


def signup(request):
    form = UserSignUpForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        UserProfile.objects.create(user=user)
        email_data = get_signup_email_confirm_form_entries(request, user)
        user.email_user(email_data['subject'], email_data['message'])
        return redirect('accounts:account_activation_sent')
    ctx = {'form': form}
    return render(request, 'accounts/signup.html', ctx)


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        userprofile = user.userprofile
        userprofile.email_confirmed = True
        userprofile.save()
        # authenticate the new user by setting his/her plain text password to a
        # unique hash
        auth_login(request, user)
        return redirect('home')
    return render(request, 'accounts/account_activation_invalid.html')


def account_activation_sent(request):
    return render(request, 'accounts/account_activation_sent.html')


@login_required
def follow_user(request, username):
    follower = request.user
    user = get_object_or_404(User, username=username)
    if user == follower:
        raise Http404
    user.userprofile.toggle_followers(follower)
    follower.userprofile.toggle_following(user)
    return redirect(user.userprofile.get_absolute_url())


def user_following(request, username):
    userprofile = get_object_or_404(UserProfile, user__username=username)
    ctx = {
        'userprofile': userprofile,
        'dropdown_active_text2': 'user_following',
    }
    return render(request, 'accounts/profile_user_following.html', ctx)


def user_followers(request, username):
    userprofile = get_object_or_404(UserProfile, user__username=username)
    ctx = {
        'userprofile': userprofile,
        'dropdown_active_text2': 'user_followers',
    }
    return render(request, 'accounts/profile_user_followers.html', ctx)


def user_mention(request):
    username = request.GET.get('username')
    if username:
        userprofile_qs = UserProfile.objects.select_related('user').filter(
            user__username__startswith=username
        )
        if userprofile_qs.exists():
            userprofile_list = get_mentioned_users_context(userprofile_qs)
            return JsonResponse({'user_list':  userprofile_list})
    return JsonResponse({'user_list': []})


def user_mention_list(request):
    username_dict_list = json.loads(request.GET.get('username_list'))
    if username_dict_list:
        username_list = [username_dict['username']
                         for username_dict in username_dict_list]
        userprofile_qs = UserProfile.objects.select_related('user').filter(
            user__username__in=username_list
        )
        if userprofile_qs.exists():
            userprofile_list = get_mentioned_users_context(userprofile_qs)
            return JsonResponse({'user_list':  userprofile_list})
    return JsonResponse({'user_list': []})
