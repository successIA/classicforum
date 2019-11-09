from forum.threads.models import Thread
from forum.threads.utils import (
    get_paginated_queryset,
    get_filtered_threads
)
from forum.core.constants import THREAD_PER_PAGE
from django.db import connection


def get_additional_category_detail_ctx(request, category, filter_str, page):
    thread_qs = Thread.objects.get_by_category(category=category)
    thread_data = get_filtered_threads(request, filter_str, thread_qs)
    thread_paginator = get_paginated_queryset(
        thread_data[1], THREAD_PER_PAGE, page
    )
    print("dropdown_active_text", thread_data[0])
    return {
        'dropdown_active_text': thread_data[0],
        'threads': thread_paginator,
        'threads_url': "/categories/%s/%s" % (category.slug, thread_data[0]),
        'form_action': category.get_thread_form_action(thread_data[0], page),
    }
