from django import template

register = template.Library()


@register.simple_tag
def common_categories(mod_profile, request_user):
    return mod_profile.get_common_categories(request_user.moderator)


@register.simple_tag
def can_hide_thread(thread, request_user):
    return request_user.moderator.can_hide_thread(thread)


@register.simple_tag
def is_thread_moderator(thread, user):
    if user.is_moderator:
        return user.moderator.is_moderating_thread(thread)
    return False


