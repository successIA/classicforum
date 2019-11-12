import json

from django.contrib.auth import login as auth_login
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.views import View
from django.shortcuts import get_object_or_404, render, redirect
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
# from django.utils import timezone

from forum.accounts.tokens import account_activation_token
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


User = get_user_model()


def user_profile_stats(request, username):
    user = get_object_or_404(User, username=username)
    comment_qs = Comment.objects.active()
    ctx = {
        'userprofile': user,
        'dropdown_active_text2': 'stats',
        'last_posted': comment_qs.get_user_last_posted(user),
        'active_category': comment_qs.get_user_active_category(user),
        'total_upvotes': comment_qs.get_user_total_upvotes(user),
        'total_upvoted': comment_qs.filter(upvoters=user).count(),
        'recent_comments': comment_qs.get_recent_for_user(user, 5),
        'recent_threads': Thread.objects.get_recent_for_user(request, user)
    }
    # return render(request, 'accounts/profile_stats.html', ctx)
    return render(request, 'accounts/profile_home.html', ctx)


@login_required
@profile_owner_required
def user_notification_list(request, username):
    page = request.GET.get('page')
    notif_qs = Notification.objects.get_for_user(request.user)
    notifs = get_paginated_queryset(notif_qs, 3, page)
    notif_id_list = [notif.pk for notif in notifs]
    print("NOTIF_IDS", notif_id_list)
    # Notification.objects.mark_all_as_read_for_receiver(request.user)
    Notification.objects.mark_as_read(request.user, notif_id_list)
    ctx = {
        'userprofile': request.user,
        'dropdown_active_text2': 'user_notifs',
        'notifications': notifs
    }
    return render(request, 'accounts/profile_notif.html', ctx)


@login_required
@profile_owner_required
def user_profile_edit(request, username):
    form = UserProfileForm(instance=request.user)
    if request.method == 'POST':
        form = UserProfileForm(
            request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            image = form.cleaned_data.get('image')
            from forum.attachments.models import Attachment
            avatar_url = Attachment.objects.create_avatar(image, request.user)
            user = form.save(commit=False)
            # To avoid deleting the user's avatar url if it is null
            # or empty string perform this check first.
            if avatar_url:
                user.avatar_url = avatar_url
            user.save()
            messages.success(request, 'Profile updated successfully!')
            username = request.user.username
            return HttpResponseRedirect(
                reverse('accounts:user_edit', kwargs={'username': username})
            )
    ctx = {
        'userprofile': request.user,
        'dropdown_active_text2': 'profile',
        'form': form
    }
    return render(request, 'accounts/profile_info.html', ctx)


def user_comment_list(request, username):
    user = User.objects.filter(username=username).first()
    comment_qs = Comment.objects.filter(user=user).exclude(
        is_starting_comment=True
    ).get_related().order_by('id')
    print("COUNT CQS", comment_qs.count())
    comments = get_paginated_queryset(comment_qs, 10, request.GET.get('page'))
    ctx = {
        'comments': comments,
        'dropdown_active_text2': 'replies',
        'userprofile': user
    }
    return render(request, 'accounts/profile_comments.html', ctx)


def user_thread_list(request, username, filter_str, page):
    user = get_object_or_404(
        User, username=username
    )
    if not user.is_required_filter_owner(request.user, filter_str):
        raise Http404
    thread_qs = Thread.objects.active()
    thread_data = get_filtered_threads(request, filter_str, thread_qs)
    thread_paginator = get_paginated_queryset(thread_data[1], 10, page)
    ctx = {
        'userprofile': user,
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
        user.email_confirmed = True
        user.save()
        # authenticate the new user by setting his/her plain text password to a
        # unique hash
        auth_login(request, user)
        return redirect('home')
    return render(request, 'accounts/account_activation_invalid.html')


def account_activation_sent(request):
    return render(request, 'accounts/account_activation_sent.html')


@login_required
def follow_user(request, username):
    follower = request.user  # john
    user = get_object_or_404(User, username=username)  # aia99
    if user == follower:
        raise Http404
    user.toggle_followers(follower)
    follower.toggle_following(user)
    return redirect(user.get_absolute_url())


def user_following(request, username):
    ctx = {
        'userprofile': get_object_or_404(User, username=username),
        'dropdown_active_text2': 'user_following',
    }
    return render(request, 'accounts/profile_user_following.html', ctx)


def user_followers(request, username):
    ctx = {
        'userprofile': get_object_or_404(User, username=username),
        'dropdown_active_text2': 'user_followers',
    }
    return render(request, 'accounts/profile_user_followers.html', ctx)


def user_mention(request):
    username = request.GET.get('username')
    user_queryset = User.objects.filter(username__startswith=username)
    if username:
        if user_queryset.exists():
            user_list = get_mentioned_users_context(user_queryset)
            return JsonResponse({'user_list':  user_list})
    return JsonResponse({'user_list': []})


def user_mention_list(request):
    username_dict_list = json.loads(request.GET.get('username_list'))
    if username_dict_list:
        username_list = [username_dict['username']
                         for username_dict in username_dict_list]
        user_qs = User.objects.select_related('user').filter(
            username__in=username_list
        )
        if user_qs.exists():
            user_list = get_mentioned_users_context(user_qs)
            return JsonResponse({'user_list':  user_list})
    return JsonResponse({'user_list': []})
