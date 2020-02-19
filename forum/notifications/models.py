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
    def notify_users(self, notif, receivers):
        notif_list = []
        for receiver in receivers:
            n = Notification(
                sender=notif.sender, 
                receiver=receiver,
                thread=notif.thread, 
                comment=notif.comment,
                notif_type=notif.notif_type
            )
            notif_list.append(n)
        if notif_list:
            self.bulk_create(notif_list)

    def mark_as_read(self, receiver, notif_id_list):
        if notif_id_list:
            self.get_for_user(
                receiver
            ).filter(unread=True, id__in=notif_id_list).update(
                unread=False, modified=timezone.now()
            )

    def get_receiver_url_and_count(self, receiver):
        qs_receiver = self.filter(receiver=receiver).select_related('receiver')
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
        return self.select_related(
            'sender', 'receiver', 'thread', 'comment'
        ).prefetch_related(
            'thread__starting_comment', 'comment__thread'
        ).filter(receiver=user).order_by('-created')


class Notification(TimeStampedModel):
    THREAD_CREATED = 'th_crd'
    THREAD_UPDATED = 'th_upd'
    COMMENT_CREATED = 'co_crd'
    COMMENT_UPVOTED = 'co_upv'
    COMMENT_LIKED = 'co_lik'
    COMMENT_REPLIED = 'co_rep'
    USER_MENTIONED = 'us_men'
    USER_FOLLOWED = 'us_fld'

    NOTIF_TYPES = (
        (THREAD_CREATED, 'created'),
        (THREAD_UPDATED, 'updated'),
        (COMMENT_CREATED, 'commented'),
        (COMMENT_UPVOTED, 'upvoted'),
        (COMMENT_LIKED, 'liked'),
        (COMMENT_REPLIED, 'posted a reply'),
        (USER_MENTIONED, 'mentioned'),
        (USER_FOLLOWED, 'following')
    )

    NOTIF_THREAD_TYPES = [THREAD_CREATED, THREAD_UPDATED]
    NOTIF_COMMENT_TYPES = [
        COMMENT_CREATED, COMMENT_UPVOTED, COMMENT_LIKED, COMMENT_REPLIED, USER_MENTIONED
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
        'threads.Thread', on_delete=models.CASCADE, null=True, blank=True
    )
    comment = models.ForeignKey(
        'comments.Comment', on_delete=models.CASCADE, null=True, blank=True
    )
    notif_type = models.CharField(max_length=6, choices=NOTIF_TYPES)
    unread = models.BooleanField(default=True)
    objects = NotificationQuerySet.as_manager()

    def __str__(self):
        return '%s (sender) - %s - %s(receiver) #%s' % (
            self.sender, self.notif_type, self.receiver, str(self.pk)
        )

    def save(self, *args, **kwargs):
        self._validate_fields()        
        super(Notification, self).save(*args, **kwargs)

    def _validate_fields(self):
        error = None
        if self.thread and self.comment:
            raise FieldError(
                'Notification cannot have both comment '
                'field and thread field set.'
            )
        if (
            self.thread and self.notif_type 
            not in Notification.NOTIF_THREAD_TYPES
        ):
            raise FieldError('Invalid notification type for field thread')
        if (
            self.comment and self.notif_type 
            not in Notification.NOTIF_COMMENT_TYPES
        ):
            raise FieldError('Invalid notification type for field comment')
        if (
            not self.thread and not self.comment and 
            self.notif_type not in Notification.NOTIF_USER_TYPES
        ):
            raise FieldError('Invalid notification type')
    
    def get_description(self):
        context = {'userprofile': self.sender, 'notif': self}
        description_dict = {
            Notification.THREAD_CREATED: 'notifications/thread_create.html',
            Notification.THREAD_UPDATED: 'notifications/thread_update.html',
            # Notification.COMMENT_CREATED: 'notifications/comment_create.html',
            Notification.COMMENT_UPVOTED: 'notifications/comment_upvote.html',
            Notification.COMMENT_LIKED: 'notifications/comment_like.html',
            Notification.COMMENT_REPLIED: 'notifications/comment_reply.html',
            Notification.USER_MENTIONED: 'notifications/comment_mention.html',
            # Notification.USER_FOLLOWED: 'notifications/thread_update.html',
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
