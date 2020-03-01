from django.http import HttpResponse
from django.shortcuts import render

from forum.threads.models import Thread
from forum.comments.models import Comment
from forum.threads.utils import get_paginated_queryset
from forum.core.constants import THREAD_PER_PAGE as PER_PAGE
from forum.core.utils import add_pagination_context


def search(request, page=1):
    query = request.GET.get('q')
    query =  query.strip() if query else ''
    is_comment = None
    results = None
    ctx = {}
    paginator = None
    if query:
        queryset = None
        if request.GET.get('search_filter') == 'comment':
            queryset = Comment.objects.active().filter(
                message__icontains=query
            ).order_by('-modified').distinct()
            is_comment = True
        else:        
            queryset = Thread.objects.active().filter(
                title__icontains=query
            ).order_by('-final_comment_time').distinct()
        paginator = get_paginated_queryset(
            queryset, PER_PAGE, page)
        base_url = ['/search/', f'/?q={query}']
        ctx['base_url'] = base_url
        add_pagination_context(base_url, ctx, paginator)
    ctx.update({ 
        'query': query,
        'results': paginator,
        'is_comment': is_comment
    })
    return render(request, 'search/search.html', ctx)    
