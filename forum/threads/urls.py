from django.conf.urls import url

from forum.threads.views import thread_list, create_thread


urlpatterns = [    
    url(r'^$', thread_list, name='thread_list'),
    url(r'(?P<filter_str>[\w-]+)/(?P<page>[\d]*)?/create/$', create_thread, name='thread_create'),
    url(r'(?P<filter_str>[\w-]+)/(?P<page>[\d]*)?/?$', thread_list, name='thread_list_filter'),
]
