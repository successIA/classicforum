import random
import re
import string

from django.http import HttpResponseRedirect
from django.utils.html import mark_safe
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings

from markdown import markdown


def get_random_string():
    s = ''.join(
        [random.choice(string.ascii_lowercase + string.digits)
         for i in range(10)]
    )
    return s.lower()


def find_images_in_message(message):
    img_regex = r'<img(?:.+?)src="(?P<src>.+?)"(?:.*?)>'
    message = mark_safe(markdown(message, safe_mode='escape'))
    return re.findall(img_regex, message)


def convert_mention_to_link(message, user_value_list):
    new_message = message
    for user in user_value_list:
        patt = r'@' + user['username']
        html = '<a class="mention" href="%s">%s</a>' % (
            user['url'], user['username']
        )
        new_message = re.sub(patt, html, new_message)
    return new_message


def find_mentioned_usernames(message):
    patt = r'@(?P<username>[\w]+)'
    return set(re.findall(patt, message))


def get_paginated_queryset(queryset, PER_PAGE, page_num):
    queryset = [] if not queryset else queryset
    paginator = Paginator(queryset, PER_PAGE)
    try:
        evaluted_qs = paginator.page(page_num)
    except PageNotAnInteger:
        evaluted_qs = paginator.page(1)
    except EmptyPage:
        evaluted_qs = paginator.page(paginator.num_pages)
    return evaluted_qs


def strip_leading_slash(text):
    leading_slash_patt = r'^/'
    return re.sub(leading_slash_patt, '', text)

def get_post_login_redirect_url(url):
    return f'{settings.LOGIN_URL}?next={url}/#comment-form'
