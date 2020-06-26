from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, reverse

from forum.categories.models import Category
from forum.core.constants import THREAD_PER_PAGE
from forum.core.utils import (
    add_pagination_context,
    get_post_login_redirect_url,
)
from forum.threads.forms import ThreadForm
from forum.threads.models import Thread
from forum.threads.utils import get_filtered_threads_for_page, get_paginated_queryset


def category_detail(request, slug, filter_str=None, page=1, form=None):    
    category = get_object_or_404(Category, slug=slug)
    thread_qs = Thread.objects.active().get_by_category(category=category)
    filter_str, filtered_qs = get_filtered_threads_for_page(
        request, filter_str, thread_qs
    )
    thread_paginator = get_paginated_queryset(
        filtered_qs, THREAD_PER_PAGE, page
    )
    category_url = category.get_precise_url(filter_str, page)
    base_url = [f'/categories/{category.slug}/{filter_str}/', '/']
    ctx = {
        'category': category,
        'form': form if form else ThreadForm(initial={'category': category}),
        'is_post_update': True if form else False,
        'current_thread_filter': filter_str,
        'threads': thread_paginator,
        'base_url': base_url,
        'show_floating_btn': True,
        'login_redirect_url': get_post_login_redirect_url(category_url),
        'form_action': category.get_thread_form_action(filter_str, page),
    }
    add_pagination_context(base_url, ctx, thread_paginator)
    return render(request, 'categories/category_detail.html', ctx)
