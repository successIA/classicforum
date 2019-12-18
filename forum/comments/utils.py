import re

from django.shortcuts import get_object_or_404
from django.utils.html import mark_safe
from django.contrib.auth import get_user_model
from django.db.models import Max, Min, Count, F, Value, CharField, Prefetch

# from forum.core.utils import find_mentioned_usernames
from forum.core.bbcode_quote import bbcode_quote
from forum.core.bbcode_quote2 import BBCodeQuoteWithMarkdownParser
from forum.core.utils import convert_mention_to_link
from forum.comments.forms import CommentForm

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
    return CommentForm.get_for_reply(message, extra='edit-message')

def find_parent_info_in_comment(message):
    text, comment_info_list = bbcode_quote(message)
    return comment_info_list
