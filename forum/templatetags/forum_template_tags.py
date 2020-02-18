from math import ceil

from django import template
from datetime import datetime, timedelta
from django.utils.timesince import timesince
from forum.core.constants import COMMENT_PER_PAGE
from forum.categories.models import Category
from forum.comments.models import Comment
from forum.threads.models import Thread

from forum.core.utils import append_querystring

register = template.Library()


@register.simple_tag
def thread_url(
    thread_absolute_url, comment_count, new_comment_id, new_comment_count
):
    try:
        if int(comment_count) <= 0 or int(new_comment_count) <= 0:
            return thread_absolute_url
        count = int(comment_count) - int(new_comment_count)
        page_num = ceil(count / COMMENT_PER_PAGE)
        if (count % COMMENT_PER_PAGE) == 0:
            page_num = page_num + 1
    except ValueError:
        return thread_absolute_url
    return '%s?page=%s&read=True#comment%s' % (
        thread_absolute_url, page_num, new_comment_id
    )


@register.filter
def splittime(value):
    return value.split(", ")[0].replace(" ago", "") + " ago"


@register.inclusion_tag('includes/category_sidebar.html')
def get_category_list(category=None):
    if category:
        return {
            'category_list': Category.objects.all(),
            'current_category': category
        }
    return {'category_list': Category.objects.all()}


@register.inclusion_tag('includes/profile_sidebar.html')
def get_profile_sidebar_list(
    request, user, dropdown_active_text2=None, is_scroller=False):
    return {
        'request': request,
        'userprofile': user,
        'dropdown_active_text2': dropdown_active_text2,
        'is_scroller': is_scroller
    }


@register.inclusion_tag('includes/thread_filter_dropdown.html')
def get_thread_filter_dropdown(
    dropdown_active_text, is_auth=False, category=None
):
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


@register.simple_tag
def url_with_page_num(url, page_number):
    return '%s?page=%s#comment-form' % (
        url, page_number
    )
    

@register.simple_tag
def precise_post_update_url(post, page_num):
    return f'{post.get_update_url()}?page={page_num}#comment-form'


@register.simple_tag
def profile_threads_text(filter_str):
    text_dict = {
        'new': 'New Threads',
        'following': 'Thread Following',
        'me': 'All Threads'
    }
    text = text_dict.get(filter_str) 
    if not text:
        text = text_dict.get('me')
    return text


@register.simple_tag
def empty_thread_description(filter_str):
    desc_dict = {
        'me': 'No threads yet',
        'new': 'No new threads yet',
        'following': 'Yet to follow any thread',
        'trending': 'No trending threads yet',
        'popular': 'No popular threads yet',
        'fresh': 'No fresh threads yet'
    }
    description = desc_dict.get(filter_str) 
    if not description:
        description = desc_dict.get('me')
    return description


@register.simple_tag
def active_category_class(dropdown_active_text2, filter_str):
    if dropdown_active_text2 == filter_str:
        return 'category-active'
    else:
        return ''


@register.filter
def paginate_url(base_url, page):
    return f"{base_url[0]}{page}{base_url[1]}"