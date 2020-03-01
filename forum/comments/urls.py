from django.conf.urls import url

from forum.comments.views import (
    create_comment,
    like_comment,
    reply_comment,
    report_comment,
    update_comment,
)

urlpatterns = [
    url(r'(?P<pk>[0-9]+)/reply/$', reply_comment, name='comment_reply'),
    url(r'(?P<pk>[0-9]+)/like/$', like_comment, name='like'),
    url(r'(?P<pk>[0-9]+)/$', update_comment, name='comment_update'),
    url(r'add/$', create_comment, name='comment_create'),
    url(r'(?P<pk>[0-9]+)/report/$', report_comment, name='report'),
]
