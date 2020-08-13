from django.conf.urls import url

from forum.categories.views import category_detail
from forum.threads.views import create_thread

app_name = 'categories'

urlpatterns = [
    url(r'^(?P<slug>[\w-]+)/$', category_detail, name='category_detail'),

    url(
        r'(?P<slug>[\w-]+)/(?P<filter_str>[\w-]+)/(?P<page>[\d]*)?/create-thread/$',
        create_thread,
        name='category_thread_create'
    ),

    url(
        r'(?P<slug>[\w-]+)/(?P<filter_str>[\w-]+)/(?P<page>[\d]*)?/?$',
        category_detail,
        name='category_detail_filter'
    ),

]
