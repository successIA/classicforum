from django import template

from forum.moderation.models import Moderator

register = template.Library()


@register.simple_tag
def common_categories(mod_profile, request_user):
    return mod_profile.get_common_categories(request_user.moderator)


@register.simple_tag
def can_hide_post(post, request_user):    
    return request_user.moderator.can_hide_post(post)


@register.filter
def post_hide_action_link(comment):
    return Moderator.get_post_hide_action_url(comment)


@register.simple_tag
def is_thread_moderator(thread, user):
    if user.is_moderator:
        return user.moderator.is_moderating_thread(thread)
    return False
