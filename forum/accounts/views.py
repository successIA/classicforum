import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View

from faker import Faker

from forum.accounts.forms import UserProfileForm, UserSignUpForm
from forum.accounts.mixins import profile_owner_required
from forum.accounts.tokens import account_activation_token
from forum.accounts.utils import (
    get_mentioned_users_context,
    get_signup_email_confirm_form_entries,
)
from forum.comments.models import Comment
from forum.core.utils import add_pagination_context, get_paginated_queryset
from forum.notifications.models import Notification
from forum.threads.models import Thread
from forum.threads.utils import get_filtered_threads_for_profile

User = get_user_model()


def user_profile_stats(request, username):
    user = get_object_or_404(User, username=username)
    comment_qs = Comment.objects.active()
    comment_count = user.comment_set.count()
    active_category = comment_qs.get_user_active_category(
        user, comment_count
    )
    ctx = {
        'userprofile': user,
        'current_profile_page': 'stats',
        'thread_count': user.thread_set.count(),
        'thread_following': user.thread_following.count(),
        'comment_count': comment_count,
        'followers': user.followers.count(),
        'following': user.following.count(),
        'last_posted': comment_qs.get_user_last_posted(user),
        'active_category': active_category,
        'total_likes': comment_qs.get_user_total_likes(user),
        'total_liked': comment_qs.filter(likers=user).count(),
        'recent_comments': comment_qs.get_recent_for_user(user, 5),
        'recent_threads': Thread.objects.get_recent_for_user(request, user)
    }
    return render(request, 'accounts/profile_home.html', ctx)


@login_required
@profile_owner_required
def user_notification_list(request, username):
    page = request.GET.get('page')
    notif_qs = Notification.objects.get_for_user(request.user)
    notifs = get_paginated_queryset(notif_qs, 3, page)
    notif_id_list = [notif.pk for notif in notifs]
    Notification.objects.mark_as_read(request.user, notif_id_list)
    notif_url, notif_count = Notification.objects.get_receiver_url_and_count(
        request.user
    )
    request.user.update_notification_info(request, notif_url, notif_count)

    base_url = [f'/accounts/{request.user.username}/notifications/?page=', '']
    ctx = {
        'userprofile': request.user,
        'current_profile_page': 'user_notifs',
        'notifications': notifs,
        'base_url': base_url
    }
    add_pagination_context(base_url, ctx, notifs)

    return render(request, 'accounts/profile_notif.html', ctx)


@login_required
@profile_owner_required
def user_profile_edit(request, username):
    form = UserProfileForm(instance=request.user)
    if request.method == 'POST':
        if settings.DEBUG:
            form = UserProfileForm(
                request.POST, request.FILES, instance=request.user
            )
        else:
            form = UserProfileForm(request.POST, instance=request.user)

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
            messages.success(request, 'Profile has been updated')
            username = request.user.username
            return HttpResponseRedirect(
                reverse('accounts:user_edit', kwargs={'username': username})
            )

    ctx = {
        'userprofile': request.user,
        'current_profile_page': 'settings',
        'form': form
    }
    return render(request, 'accounts/profile_edit.html', ctx)


def user_comment_list(request, username):
    user = get_object_or_404(User, username=username)
    comment_qs = Comment.objects.get_pure_and_thread_active_for_user(user)
    comments = get_paginated_queryset(comment_qs, 10, request.GET.get('page'))
    url = reverse('accounts:user_comments', kwargs={'username':  username})
    base_url = [f'{url}?page=', '']
    ctx = {
        'comments': comments,
        'base_url': base_url,
        'current_profile_page': 'replies',
        'userprofile': user
    }
    add_pagination_context(base_url, ctx, comments)
    return render(request, 'accounts/profile_comments.html', ctx)


def user_thread_list(request, username, filter_str, page):
    user = get_object_or_404(User, username=username)
    if not user.is_required_filter_owner(request.user, filter_str):
        raise Http404
    thread_qs = Thread.objects.active()
    filter_str, filtered_qs = get_filtered_threads_for_profile(
        request, filter_str, thread_qs, user=user
    )
    thread_paginator = get_paginated_queryset(filtered_qs, 10, page)
    base_url = [f'/accounts/{username}/{filter_str}/', '/']
    ctx = {
        'userprofile': user,
        'threads': thread_paginator,
        'base_url': base_url,
        'current_profile_page': filter_str
    }
    add_pagination_context(base_url, ctx, thread_paginator)
    return render(request, 'accounts/profile_threads.html', ctx)


def signup(request):
    form = UserSignUpForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        if settings.CONFIRM_EMAIL and user.email:
            user.is_active = False
            user.save()
            email_data = get_signup_email_confirm_form_entries(request, user)
            user.email_user(email_data['subject'], email_data['message'])
            return redirect('accounts:account_activation_sent')
        else:
            user.save()
            auth_login(request, user)
            return redirect('home')

    ctx = {'form': form}
    return render(request, 'accounts/signup.html', ctx)


def guest_signup(request):
    if request.method != 'POST':
        raise Http404
    
    user = User()
    suffix = get_random_string(length=10).lower()
    user.username = f'guest_{suffix}'
    user.save()
    auth_login(request, user)
    return redirect('home')


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
        return render(
            request, 'accounts/account_activation_success.html'
        )
    return render(request, 'accounts/account_activation_invalid.html')


def account_activation_sent(request):
    return render(request, 'accounts/account_activation_sent.html')


@login_required
def follow_user(request, username):
    user = get_object_or_404(User, username=username)
    if request.method == 'POST':        
        follower = request.user 
        if user == follower:
            raise Http404
        is_follower = user.toggle_followers(follower)
        if request.is_ajax():
            return JsonResponse({'is_follower': is_follower})
    return redirect(user.get_absolute_url())


def user_following(request, username):
    user = get_object_or_404(User, username=username)
    user_following = user.following.prefetch_related('following').all()
    ctx = {
        'userprofile': user,
        'user_following': user_following,
        'current_profile_page': 'user_following',
    }
    return render(request, 'accounts/profile_user_following.html', ctx)


def user_followers(request, username):
    user = get_object_or_404(User, username=username)
    user_followers = user.followers.prefetch_related('followers').all()
    ctx = {
        'userprofile': user,
        'user_followers': user_followers,
        'current_profile_page': 'user_followers',
    }
    return render(request, 'accounts/profile_user_followers.html', ctx)


def user_mention(request):
    username = request.GET.get('username')
    user_queryset = User.objects.filter(
        username__istartswith=username
    ).order_by('username')[:8]
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
        user_qs = User.objects.filter(
            username__in=username_list
        )
        if user_qs.exists():
            user_list = get_mentioned_users_context(user_qs)
            return JsonResponse({'user_list':  user_list})
    return JsonResponse({'user_list': []})
