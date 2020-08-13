from math import ceil

from django.conf import settings
from django.core.exceptions import FieldError
from django.urls import reverse
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone

from forum.core.constants import NOTIF_PER_PAGE
from forum.core.models import TimeStampedModel


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
    COMMENT_LIKED = 'co_lik'
    COMMENT_REPLIED = 'co_rep'
    USER_MENTIONED = 'us_men'
    USER_FOLLOWED = 'us_fld'

    NOTIF_TYPES = (
        (THREAD_CREATED, 'started a new thread:'),
        (THREAD_UPDATED, 'updated a thread you are following:'),
        (COMMENT_LIKED, 'liked your comment in'),
        (COMMENT_REPLIED, 'replied to your comment in'),
        (USER_MENTIONED, 'mentioned you in a comment in'),
        (USER_FOLLOWED, 'is now following you')
    )

    NOTIF_THREAD_TYPES = [THREAD_CREATED, THREAD_UPDATED]
    NOTIF_COMMENT_TYPES = [
        COMMENT_LIKED, COMMENT_REPLIED, USER_MENTIONED
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
        self._validate_fields_or_error()        
        super(Notification, self).save(*args, **kwargs)

    def _validate_fields_or_error(self):
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
        return render_to_string(
            'notifications/notification.html', {'notif': self}
        )

    def get_precise_url(self, position):
        page_num = ceil(position / NOTIF_PER_PAGE)
        return '%s?page=%s' % (
            reverse(
                'accounts:user_notifs',
                kwargs={'username': self.receiver.username}
            ),
            page_num
        )

    @property
    def action_object_verb(self):
        return dict(Notification.NOTIF_TYPES)[self.notif_type]
    
    @property
    def action_object_title(self):
        if self.notif_type in Notification.NOTIF_COMMENT_TYPES:
            return self.comment.thread.title
        elif self.notif_type in Notification.NOTIF_THREAD_TYPES:
            return self.thread.title
        return None

    @property
    def action_object_message(self):
        if self.notif_type in Notification.NOTIF_COMMENT_TYPES:
            return self.comment.marked_message
        elif self.notif_type in Notification.NOTIF_THREAD_TYPES:
            return self.thread.starting_comment.marked_message
        return None
    
    @property
    def action_object_url(self):
        if self.notif_type in Notification.NOTIF_COMMENT_TYPES:
            return self.comment.get_precise_url()
        elif self.notif_type in Notification.NOTIF_THREAD_TYPES:
            return self.thread.get_absolute_url()
        elif self.notif_type in Notification.NOTIF_USER_TYPES:
            return self.sender.get_absolute_url()
