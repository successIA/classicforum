from django.conf.urls import url

from forum.comments.views import (
    create_comment,
    update_comment,
    reply_comment,
    upvote_comment,
    downvote_comment,
    report_comment,
)

urlpatterns = [
    url(r'(?P<pk>[0-9]+)/reply/$', reply_comment, name='comment_reply'),
    url(r'(?P<pk>[0-9]+)/upvote/$', upvote_comment, name='upvote'),
    url(r'(?P<pk>[0-9]+)/downvote/$', downvote_comment, name='downvote'),
    url(r'(?P<pk>[0-9]+)/$', update_comment, name='comment_update'),
    url(r'add/$', create_comment, name='comment_create'),
    url(r'(?P<pk>[0-9]+)/report/$', report_comment, name='report'),
]

