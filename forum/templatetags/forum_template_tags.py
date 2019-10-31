from django import template

from forum.categories.models import Category

register = template.Library()


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
    RECENT:'Recent',
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
def get_profile_sidebar_list(request, userprofile, dropdown_active_text2=None):
    return {
        'request': request,
        'userprofile': userprofile,
        'dropdown_active_text2': dropdown_active_text2,
    }
