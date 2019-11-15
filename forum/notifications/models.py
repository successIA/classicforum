from math import ceil

from django.db import models
from django.conf import settings
from django.template.loader import render_to_string
from django.core.exceptions import FieldError
from django.utils import timezone
from django.core.urlresolvers import reverse

from forum.core.models import TimeStampedModel
from forum.core.constants import NOTIF_PER_PAGE


class NotificationQuerySet(models.query.QuerySet):
    def notify_receiver_for_reply(self, reply):
        self.create(
            sender=reply.user,
            receiver=reply.parent.user,
            comment=reply,
            notif_type=Notification.COMMENT_REPLIED
        )

    def notify_mentioned_users(self, comment, mentioned_user_list):
        users = [usr for usr in mentioned_user_list if usr.pk != comment.user.pk]
        model_list = []
        for user in users:
            model_list.append(
                self.model(
                    sender=comment.user,
                    receiver=user,
                    comment=comment,
                    notif_type=Notification.USER_MENTIONED
                )
            )
        self.bulk_create(model_list)

    def notify_user_followers_for_thread_creation(self, thread):
        model_list = []
        for user in thread.user.followers.all():
            model_list.append(
                self.model(
                    sender=thread.user,
                    receiver=user,
                    thread=thread,
                    notif_type=Notification.THREAD_CREATED
                )
            )
        self.bulk_create(model_list)

    def notify_thread_followers_for_modification(self, thread):
        other_followers = [usr for usr in thread.followers.all()
                           if usr.pk != thread.user.pk]
        for user in other_followers:
            self.create(
                sender=thread.user,
                receiver=user,
                thread=thread,
                notif_type=Notification.THREAD_UPDATED
            )

    def notify_receiver_for_comment_upvote(self, sender, receiver, comment):
        self.create(
            sender=sender,
            receiver=receiver,
            comment=comment,
            notif_type=Notification.COMMENT_UPVOTED
        )

    def delete_comment_upvote_notification(self, sender, receiver, comment):
        queryset = self.filter(
            sender=sender,
            receiver=receiver,
            comment=comment,
            notif_type=Notification.COMMENT_UPVOTED
        ).first().delete()

    def mark_as_read(self, receiver, notif_id_list):
        if notif_id_list:
            self.get_for_user(
                receiver
            ).filter(unread=True, id__in=notif_id_list).update(
                unread=False, modified=timezone.now()
            )

    def get_receiver_url_and_count(self, receiver):
        qs_receiver = self.filter(receiver=receiver)
        unread_qs = list(qs_receiver.filter(
            unread=True
        ).order_by('-created'))
        position = 0
        url = ''
        if len(unread_qs) > 0 and unread_qs[0]:
            for model in qs_receiver.order_by('-created'):
                position = position + 1
                if model.pk == unread_qs[0].pk:
                    break
            if position:
                url = model.get_precise_url(position)

        if not url:
            url = reverse(
                'accounts:user_notifs', kwargs={'username': receiver.username}
            )
        count = len(unread_qs)
        return url, count

    def get_for_user(self, user):
        return Notification.objects.select_related(
            'sender', 'receiver', 'thread', 'comment'
        ).prefetch_related(
            'thread__starting_comment', 'comment__thread'
        ).filter(receiver=user).order_by('-created')


class Notification(TimeStampedModel):
    THREAD_CREATED = 'th_crd'
    THREAD_UPDATED = 'th_upd'
    COMMENT_CREATED = 'co_crd'
    COMMENT_UPVOTED = 'co_upv'
    COMMENT_REPLIED = 'co_rep'
    USER_MENTIONED = 'us_men'
    USER_FOLLOWED = 'us_fld'

    NOTIF_TYPES = (
        (THREAD_CREATED, 'created'),
        (THREAD_UPDATED, 'updated'),
        (COMMENT_CREATED, 'commented'),
        (COMMENT_UPVOTED, 'upvoted'),
        (COMMENT_REPLIED, 'posted a reply'),
        (USER_MENTIONED, 'mentioned'),
        (USER_FOLLOWED, 'following')
    )

    NOTIF_THREAD_TYPES = [THREAD_CREATED, THREAD_UPDATED]
    NOTIF_COMMENT_TYPES = [
        COMMENT_CREATED, COMMENT_UPVOTED, COMMENT_REPLIED, USER_MENTIONED
    ]
    NOTIF_USER_TYPES = [USER_FOLLOWED]

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sender_notif'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='receiver_notif'
    )
    thread = models.ForeignKey(
        'threads.Thread', on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(
        'comments.Comment', on_delete=models.CASCADE, null=True, blank=True)
    notif_type = models.CharField(max_length=6, choices=NOTIF_TYPES)
    unread = models.BooleanField(default=True)
    objects = NotificationQuerySet.as_manager()

    def __str__(self):
        return '%s (sender) - %s - %s(receiver) #%s' % (
            self.sender, self.notif_type, self.receiver, str(self.pk)
        )

    def save(self, *args, **kwargs):
        error = None
        if self.thread and self.comment:
            raise FieldError(
                'Notification cannot have both comment field and thread field set.'
            )
        if self.thread and self.notif_type not in Notification.NOTIF_THREAD_TYPES:
            raise FieldError('Invalid notification type for field thread')
        if self.comment and self.notif_type not in Notification.NOTIF_COMMENT_TYPES:
            raise FieldError('Invalid notification type for field comment')
        if not self.thread and not self.comment and self.notif_type not in Notification.NOTIF_USER_TYPES:
            raise FieldError('Invalid notification type')
        super().save(*args, **kwargs)

    def get_description(self):
        context = {'userprofile': self.sender, 'notif': self}
        description_dict = {
            Notification.THREAD_CREATED: 'notifications/thread_create.html',
            Notification.THREAD_UPDATED: 'notifications/thread_update.html',
            Notification.COMMENT_CREATED: 'notifications/comment_create.html',
            Notification.COMMENT_UPVOTED: 'notifications/comment_upvote.html',
            Notification.COMMENT_REPLIED: 'notifications/comment_reply.html',
            Notification.USER_MENTIONED: 'notifications/comment_mention.html',
            Notification.USER_FOLLOWED: 'notifications/thread_update.html',
        }
        return render_to_string(description_dict[self.notif_type], context)

    def get_precise_url(self, position):
        page_num = ceil(position / NOTIF_PER_PAGE)
        return '%s?page=%s' % (
            reverse(
                'accounts:user_notifs',
                kwargs={'username': self.receiver.username}
            ),
            page_num
        )
