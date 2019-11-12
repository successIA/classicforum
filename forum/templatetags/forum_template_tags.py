from django import template
from datetime import datetime, timedelta
from django.utils.timesince import timesince

from forum.categories.models import Category

register = template.Library()


@register.filter
def splittime(value):
    return value.split(", ")[0].replace(" ago", "") + " ago"


@register.inclusion_tag('forum/categories_template.html')
def get_category_list(category=None):
    if category:
        return {
            'category_list': Category.objects.all(),
            'current_category': category
        }
    return {'category_list': Category.objects.all()}


DEFAULT_FILTER_TEXT = 'Filter'

RECENT = 'recent'
TRENDING = 'trending'
POPULAR = 'popular'
SOLVED = 'solved'
UNSOLVED = 'unsolved'
NO_REPLY = 'fresh'

all_dropdown_text_dict = {
    RECENT: 'Recent',
    TRENDING: 'Trending (this week)',
    POPULAR: 'Trending (all time)',
    SOLVED: 'Solved',
    UNSOLVED: 'Unsolved',
    NO_REPLY: 'No Response Yet',
}

NEW = 'new'
FOLLOWING = 'following'
ME = 'me'
UNREAD = 'unread'

user_dropdown_text_dict = {
    NEW: 'New',
    FOLLOWING: 'Following',
    ME: 'For Me',
    UNREAD: 'Unread'
}


@register.inclusion_tag('forum/all_threads_dropdown_template.html')
def get_all_threads_dropdown_list(dropdown_active_text=None, category=None):
    return {
        'all_dropdown_text_dict': all_dropdown_text_dict,
        'dropdown_active_text': dropdown_active_text,
        'category': category
    }


@register.filter
def dropdown_text_value(key):
    text = all_dropdown_text_dict.get(key, None)
    if not text:
        return DEFAULT_FILTER_TEXT
    return text


@register.inclusion_tag('forum/user_threads_dropdown_template.html')
def get_user_threads_dropdown_list(dropdown_active_text2=None, category=None):
    return {
        'user_dropdown_text_dict': user_dropdown_text_dict,
        'dropdown_active_text2': dropdown_active_text2,
        'category': category
    }


@register.filter
def dropdown_text_value2(key):
    text = user_dropdown_text_dict.get(key, None)
    if not text:
        return DEFAULT_FILTER_TEXT
    return text


profile_sidebar_dict = {
    'stats': 'Profile Info',
    'notifications': 'Notifications',
    'profile': 'Settings',
    'replies': 'Replies',
    'new': 'New',
    'following': 'Following',
    'me': 'Threads',
    'user_following': 'User Following',
    'user_followers': 'User Following',
}


@register.inclusion_tag('includes/profile_sidebar.html')
def get_profile_sidebar_list(request, user, dropdown_active_text2=None):
    return {
        'request': request,
        'userprofile': user,
        'dropdown_active_text2': dropdown_active_text2,
    }


@register.inclusion_tag('forum/filter_dropdown_body.html')
def get_filter_dropdown_body(dropdown_active_text, is_auth=False, category=None):
    filter_list = None
    if is_auth:
        filter_list = [
            ('new', 'New'),
            ('following', 'Following'),
            ('me', 'For Me'),
        ]
    else:
        filter_list = [
            ('trending', 'Trending'),
            ('popular', 'Popular'),
            ('fresh', 'No Replies')
        ]
    context = {
        'filter_dropdown_list': filter_list,
        'filter_dropdown_list_item_keys': [k for k, v in filter_list],
        'dropdown_active_text': dropdown_active_text,
        'filter_text': "Personalise" if is_auth else "Filter"
    }
    if category:
        context.update({'category': category})
    return context


@register.filter
def home_pagination_url(threads_url, page_num):
    return "%s/%s" % (threads_url, page_num)
