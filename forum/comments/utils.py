import re

from django.shortcuts import get_object_or_404
from django.utils.html import mark_safe
from django.contrib.auth import get_user_model
from django.db.models import Max, Min, Count, F, Value, CharField, Prefetch

# from forum.core.utils import find_mentioned_usernames
from forum.core.bbcode_quote import bbcode_quote
from forum.core.bbcode_quote2 import BBCodeQuoteWithMarkdownParser
from forum.core.utils import (
    convert_mention_to_link,
    find_mentioned_usernames
)
from forum.comments.forms import CommentForm
from forum.accounts.utils import get_user_list_without_creator
from forum.attachments.models import Attachment
from forum.threads.models import ThreadFollowership
from forum.notifications.models import Notification

from markdown import markdown

User = get_user_model()


def get_rendered_message(message, user_value_list):
    message = convert_mention_to_link(message, user_value_list)
    rendered_message = BBCodeQuoteWithMarkdownParser(message).parse()
    return rendered_message


def get_bbcode_message_quote(parent_comment):
    open_quote_tag = f'[quote="{parent_comment.user.username}, comment:{parent_comment.id}"]\n'
    close_quote_tag = '\n[/quote]\n'
    return f'{open_quote_tag}{parent_comment.message}{close_quote_tag}'


def get_comment_reply_form(comment):
    message = get_bbcode_message_quote(comment)
    return CommentForm.get_for_reply(message)


def find_parent_info_in_comment(message):
    text, comment_info_list = bbcode_quote(message)
    return comment_info_list


def get_user_value_list(user_list):
    return [
        {'username': usr.username, 'url': usr.get_absolute_url()}
        for usr in user_list
    ]


def get_mentioned_users_in_message(message):
    mentions = find_mentioned_usernames(message)
    mentioned_user_list = list(
        User.objects.filter(username__in=mentions).all()
    )
    return mentioned_user_list


def create_comment_revision(comment):
    from forum.comments.models import CommentRevision
    
    revision = CommentRevision.objects.create(
        comment=comment,
        message=comment.message,
        marked_message=comment.marked_message,            
    )
    revision.mentioned_users.add(*comment.mentioned_users.all())


def perform_comment_save(comment, prev_msg=None):
    is_pure_comment_create = (True if not comment.pk 
        and not comment.is_starting_comment else False
    )
    
    if is_pure_comment_create: comment.set_position()    
    mentions = comment.set_message()
    comment.save()

    if is_pure_comment_create:
        _perform_comment_post_create_actions(comment)
    
    _perform_comment_post_save_actions(comment, prev_msg, mentions)


def _perform_comment_post_create_actions(comment):
    comment.thread.synchronise(comment)
    ThreadFollowership.objects.synchronise(comment.thread, comment)


def _perform_comment_post_save_actions(comment, prev_msg, mentions):
    comment.mentioned_users.add(*mentions)
    Attachment.objects.synchronise(comment, prev_msg)
    user_list = get_user_list_without_creator(mentions, comment.user)
    notif = Notification(
        sender=comment.user,
        comment=comment,
        notif_type=Notification.USER_MENTIONED
    )
    # TODO A notification should not be sent if comment or thread is
    # is invisible
    Notification.objects.notify_users(notif, user_list)

