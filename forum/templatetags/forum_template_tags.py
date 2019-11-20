from math import ceil

from django import template
from datetime import datetime, timedelta
from django.utils.timesince import timesince
from forum.core.constants import COMMENT_PER_PAGE
from forum.categories.models import Category

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


@register.inclusion_tag('includes/categories_template.html')
def get_category_list(category=None):
    if category:
        return {
            'category_list': Category.objects.all(),
            'current_category': category
        }
    return {'category_list': Category.objects.all()}


@register.inclusion_tag('includes/profile_sidebar.html')
def get_profile_sidebar_list(request, user, dropdown_active_text2=None):
    return {
        'request': request,
        'userprofile': user,
        'dropdown_active_text2': dropdown_active_text2,
    }


@register.inclusion_tag('includes/filter_dropdown_body.html')
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


@register.simple_tag
def url_with_page_num(url, page_number):
    return '%s?page=%s#comment-form' % (
        url, page_number
    )
