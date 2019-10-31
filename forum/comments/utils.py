import re

from django.shortcuts import get_object_or_404
from django.utils.html import mark_safe
from django.contrib.auth.models import User
from django.db.models import Max, Min, Count, F, Value, CharField, Prefetch

from forum.comments.models import Comment, CommentRevision
from forum.comments.forms import CommentForm
from forum.core.utils import find_mentioned_usernames
from forum.attachments.utils import associate_attachment_with_comment
from forum.core.bbcode_quote import bbcode_quote
from forum.core.utils import convert_mention_to_link
from forum.notifications.utils import (
    send_notif_to_mentioned_users,
    notify_receiver_for_reply
)
from forum.threads.utils import (
    create_thread_followership,
    increase_thread_comment_count,
    notify_thread_followers_for_comment,
)

from markdown import markdown
import bleach
from bleach_whitelist import markdown_tags, markdown_attrs


def save_comment(comment):
    comment = comment
    message = bleach.clean(comment.message, markdown_tags, markdown_attrs)
    comment.message = message
    if not comment.pk:
        print('performing create')
        _create(comment)
    else:
        print('performing update with comment.pk: ', comment.pk)
        _update(comment)
    comment.mentioned_users = get_mentioned_users(comment.message)
    comment.marked_message = get_rendered_message(comment)
    comment.save()
    send_notif_to_mentioned_users(comment)
    return comment
    

def _create(comment):
    comment.position = comment.thread.comments.count() + 1
    comment.save()
    userprofile = comment.user.userprofile
    associate_attachment_with_comment(comment)
    create_thread_followership(userprofile, comment.thread)
    thread = increase_thread_comment_count(
        comment.thread, comment.user, comment.created
    )
    notify_thread_followers_for_comment(comment.user, comment, thread)
    if comment.parent and comment.parent.user != comment.user:
        notify_receiver_for_reply(comment)


def _update(comment):
    old_comment = get_object_or_404(Comment, pk=comment.pk)
    associate_attachment_with_comment(comment, old_comment)
    comment_revision = CommentRevision(
        comment=comment, 
        message=old_comment.message, 
        marked_message=old_comment.marked_message
    )
    comment_revision.save()
    comment_revision.mentioned_users = old_comment.mentioned_users.all()
    comment_revision.save()
    comment.save()


def get_rendered_message(comment):
    message = convert_mention_to_link(comment.message, comment.mentioned_users)
    text, comment_info_list = bbcode_quote(message)
    text = markdown(text, safe_mode='escape')
    return mark_safe(text)


def get_mentioned_users(message):
    username_set = find_mentioned_usernames(message)
    return User.objects.filter(username__in=username_set)


def get_bbcode_message_quote(parent_comment):
    quote_open = '[quote="%s, comment:%d"] \n' % (
        parent_comment.user.username, parent_comment.id
    )
    quote_close = '\n[/quote] \n'
    return '%s%s%s' % (quote_open, parent_comment.message, quote_close)


def get_comment_reply_form(comment):
    message = get_bbcode_message_quote(comment)
    return CommentForm.get_for_reply(message, extra='edit-message') 


def find_parent_info_in_comment(message):
    text, comment_info_list = bbcode_quote(message)
    return comment_info_list


def add_comment_to_parents(comment_info_list, new_comment):
    comment_info_list = normalize_comment_info_list(comment_info_list)
    for comment_info in comment_info_list:
        username = comment_info['username'].strip()
        comment_id = comment_info['id'].strip()
        try:
            comment_qs = Comment.objects.filter(
                pk=int(comment_id), user__username=username
            )
            if comment_qs.exists():
                comment = comment_qs.first()
                comment.children.add(new_comment)
        except:
            continue


def normalize_comment_info_list(comment_info_list):
    key_list = []
    normalized_list = []
    for comment_info in comment_info_list:
        username = comment_info['username']
        comment_id = comment_info['id']
        key = '%s%s' % (username.strip(), comment_id.strip())
        if key not in key_list:
            key_list.append(key)
            normalized_list.append(comment_info)
    return normalized_list


def set_just_commented(request, comment):
    key = '%s%s' % (str(comment.thread.slug), '_just_commented')
    request.session[key] = True
    return request

