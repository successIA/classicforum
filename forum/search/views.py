from django.http import HttpResponse
from django.shortcuts import render

from forum.threads.models import Thread
from forum.threads.utils import get_paginated_queryset
from forum.core.constants import THREAD_PER_PAGE
from forum.core.utils import add_pagination_context


def search(request, page=1):
    query = request.GET.get('q')
    query =  query.strip() if query else ''
    results = None
    ctx = {}
    thread_paginator = None
    if query:        
        thread_qs = Thread.objects.active().filter(
            title__icontains=query
        ).order_by('-final_comment_time').distinct()
        thread_paginator = get_paginated_queryset(
            thread_qs, THREAD_PER_PAGE, page)
        base_url = ['/search/', f'/?q={query}']
        ctx['base_url'] = base_url
        add_pagination_context(base_url, ctx, thread_paginator)
    ctx.update({ 
        'query': query,
        'results': thread_paginator 
    })
    return render(request, 'search/search.html', ctx)    
