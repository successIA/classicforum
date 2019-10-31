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
        'message' : render_to_string(
            'accounts/account_activation_email.html', ctx
        )
    }


def get_mentioned_users_context(userprofile_qs):
    userprofile_list = []
    for userprofile in userprofile_qs:
        if userprofile.attachment_set.count() > 0:
            url = userprofile.attachment_set.first().image.url 
        else:
            url = '/static/img/avatar.svg'
        userprofile_list.append({
            'username': userprofile.user.username, 
            'profile_url': userprofile.get_absolute_url(),
            'avatar_url': url
        })
    return userprofile_list

