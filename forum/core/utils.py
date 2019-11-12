import re

from django.http import HttpResponseRedirect
from django.utils.html import mark_safe
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from markdown import markdown


def find_images_in_message(message):
    img_regex = r'<img(?:.+?)src="(?P<src>.+?)"(?:.*?)>'
    message = mark_safe(markdown(message, safe_mode='escape'))
    return re.findall(img_regex, message)


def convert_mention_to_link(message, user_qs):
    print('user_qs.all(): ', user_qs.all())
    new_message = message
    for user in user_qs.all():
        patt = r'@' + user.username
        html = '<a class="mention" href="' + user.get_absolute_url() + '">' + \
            user.username + '</a>'
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
