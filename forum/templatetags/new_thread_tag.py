from django import template

from math import ceil

register = template.Library()


@register.filter
def old_thread_indicator(thread_absolute_url):
    list_thread_absolute_url = thread_absolute_url.split('#')[0]
    str_thread_absolute_url = ''.join(list_thread_absolute_url)
    return str_thread_absolute_url


@register.filter
def is_new_thread(thread_absolute_url):
    list_thread_absolute_url = thread_absolute_url.split('#')
    if len(list_thread_absolute_url) > 1:
        return True
    return False

@register.simple_tag
def thread_url(
    thread_absolute_url, comment_count, new_comment_id, new_comment_count
):
    try:
        if int(comment_count) <= 0 or int(new_comment_count) <=0:
            return thread_absolute_url
        count = int(comment_count) - int(new_comment_count)
        PER_PAGE = 5
        page_num = ceil(count / PER_PAGE)
        if (count % PER_PAGE) == 0:
            page_num = page_num + 1
    except ValueError:
        return thread_absolute_url     
    return '%s?page=%s&read=True#comment%s' % (
        thread_absolute_url, str(page_num), str(new_comment_id)
    )

@register.simple_tag
def comment_precise_url(url, page_number, comment_id):
    return '%s?page=%s&read=True#comment%s' % (
            url, str(page_number), comment_id
    )  

@register.simple_tag
def comment_edit_url(url, page_number):
    return '%s?page=%s#comment-form' % (
            url, str(page_number) 
    )   

@register.simple_tag
def thread_edit_url(url, page_number):
    return '%sedit/?page=%s' % (
            url, str(page_number) 
    )


    

