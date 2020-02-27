import random
import re
import string

from django.http import HttpResponseRedirect
from django.utils.html import mark_safe
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings

from hitcount.models import HitCount
from hitcount.views import HitCountMixin
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


def create_hit_count(request, instance):
    hit_count = HitCount.objects.get_for_object(instance)
    hit_count_response = HitCountMixin.hit_count(request, hit_count)


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


def add_pagination_context(base_url, context, paginator):
    # TODO Match the last occurence of %s in the base_url
    number = paginator.number
    if paginator.has_next():
        number = paginator.next_page_number()
        context["next_url"] = f"{base_url[0]}{number}{base_url[1]}"
    if paginator.has_previous():
        number = paginator.previous_page_number()
        context["prev_url"] = f"{base_url[0]}{number}{base_url[1]}"


def strip_leading_slash(text):
    leading_slash_patt = r'^/'
    return re.sub(leading_slash_patt, '', text)


def get_post_login_redirect_url(url):
    return f'{settings.LOGIN_URL}?next={url}/#post-form'


def append_querystring(url, querystring):
    if "?" in url:
        return f"{url}&{querystring}"
    return f"{url}?{querystring}"
