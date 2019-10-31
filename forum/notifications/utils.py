from django.contrib.auth.models import User

from forum.comments.models import Comment
from forum.notifications.models import Notification
from forum.core.utils import find_mentioned_usernames

import re


def notify_thread_followers_for_creation(thread):
    for user in thread.user.userprofile.followers.all():
        Notification.objects.create(
            sender=thread.user, 
            receiver=user,
            thread=thread, 
            notif_type=Notification.THREAD_CREATED
        )

def notify_thread_followers_for_update(thread):
    other_followers = thread.followers.exclude(
        threadfollowership__userprofile=thread.user.userprofile
    )
    for userprofile in other_followers.all():
        Notification.objects.get_or_create(
            sender=thread.user, 
            receiver=userprofile.user,
            thread=thread, 
            notif_type=Notification.THREAD_UPDATED
        )

def notify_receiver_for_reply(comment):
    if comment.parent and comment.parent.user != comment.user:
        Notification.objects.create(
            sender=comment.user, 
            receiver=comment.parent.user,
            comment=comment, 
            notif_type=Notification.COMMENT_REPLIED
        )

def delete_comment_upvote_notif(user, comment):
    notif_qs = Notification.objects.filter(
        sender=user, 
        receiver=comment.user,
        comment=comment, 
        notif_type=Notification.COMMENT_UPVOTED
    )
    if notif_qs.exists():
        notif_qs.first().delete()

def send_notif_to_mentioned_users(comment):
    if comment.revisions.count() > 0:
        rev_comment = comment.revisions.latest('created')
        delete_unmentioned_user_notif(comment)
    user_qs = comment.mentioned_users.exclude(pk=comment.user.pk)
    for user in user_qs.all():
        Notification.objects.create(
            sender=comment.user, 
            receiver=user,
            comment=comment, 
            notif_type=Notification.USER_MENTIONED
        )
    
def delete_unmentioned_user_notif(comment):
    if comment.mentioned_users.count() > 0:
        for user in comment.mentioned_users.all():
            notif_qs = Notification.objects.filter(
                sender=comment.user, 
                receiver=user,
                comment=comment, 
                notif_type=Notification.USER_MENTIONED
            )
            if notif_qs.exists():
                notif_qs.first().delete()

