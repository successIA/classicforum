from django.conf.urls import url

from .views import (
    create_moderator,
    moderator_detail,
    update_moderator,
    delete_moderator,
    moderator_list,

    hide_thread,
    unhide_thread,

    hide_comment,
    unhide_comment,
)

urlpatterns = [
    url(r'^add/$', create_moderator, name='moderator_create'),
    url(
        r'^(?P<username>[\w-]+)/detail/$', moderator_detail, name='moderator_detail'
    ),
    url(
        r'^(?P<username>[\w-]+)/edit/$', update_moderator, name='moderator_update'
    ),
    url(
        r'^(?P<username>[\w-]+)/delete/$', delete_moderator, name='moderator_delete'
    ),
    url(r'^list/$', moderator_list, name='moderator_list'),

    url(r'^topics/(?P<slug>[\w-]+)/hide/$', hide_thread, name='thread_hide'),
    url(r'^topics/(?P<slug>[\w-]+)/unhide/$', unhide_thread, name='thread_unhide'),

    url(
        r'^topics/(?P<thread_slug>[\w-]+)/(?P<comment_pk>[\w-]+)/hide/$', 
        hide_comment, 
        name='comment_hide'
    ),
    url(
        r'^topics/(?P<thread_slug>[\w-]+)/(?P<comment_pk>[\w-]+)/unhide/$', 
        unhide_comment, 
        name='comment_unhide'
    ),
]

