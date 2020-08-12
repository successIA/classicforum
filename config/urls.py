from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin

import debug_toolbar

from forum.threads.views import (
    follow_thread,
    thread_detail,
    thread_list,
    update_thread,
)

def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    url('__debug__/', include(debug_toolbar.urls)),
    url(r'^sentry-debug/', trigger_error),

    url(r'^$', thread_list, name='home'),
    url(r'^categories/', include('forum.categories.urls', namespace='categories')),
    url(r'^threads/', include('forum.threads.urls', namespace='threads')),
    url(r'^accounts/', include('forum.accounts.urls', namespace='accounts')),
    url(r'^(?P<thread_slug>[\w-]+)/follow/$', follow_thread, name='thread_follow'),
    url(r'^topics/(?P<thread_slug>[\w-]+)/$', thread_detail, name='thread_detail'),
    url(r'^topics/(?P<thread_slug>[\w-]+)/edit/$', update_thread, name='thread_update'),
    url(r'^topics/(?P<thread_slug>[\w-]+)/comments/', include('forum.comments.urls', namespace='comments')),
    url(r'^upload/', include('forum.attachments.urls', namespace='attachments')),

    url(r'^search/', include('forum.search.urls', namespace='search')),
    url(r'^moderation/', include('forum.moderation.urls', namespace='moderation')),
    url(settings.ADMIN_URL, admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
