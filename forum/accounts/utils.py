from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string

from forum.accounts.tokens import account_activation_token


def get_signup_email_confirm_form_entries(request, user):
    ctx = {
        'user': user,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user)
    }
    return {
        'subject': 'Activate Your Forum Account',
        'message': render_to_string(
            'accounts/account_activation_email.html', ctx
        )
    }


def get_mentioned_users_context(user_qs):
    user_list = []
    for user in user_qs:
        if user.avatar_url:
            url = user.avatar_url
        else:
            url = '/static/img/avatar.svg'
        user_list.append({
            'username': user.username,
            'profile_url': user.get_absolute_url(),
            'avatar_url': url
        })
    return user_list


def get_user_list_without_creator(users, creator):
    return [usr for usr in users if usr.pk != creator.pk]
    