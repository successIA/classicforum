from math import ceil

from django.db import models
from django.conf import settings
from django.template.loader import render_to_string
from django.core.exceptions import FieldError
from django.utils import timezone
from django.core.urlresolvers import reverse

from forum.threads.models import Thread
from forum.comments.models import Comment
from forum.core.models import TimeStampedModel


class NotificationQuerySet(models.query.QuerySet):
    def notify_receiver_for_reply(self, reply):
        self.create(
            sender=reply.user,
            receiver=reply.parent.user,
            comment=reply,
            notif_type=Notification.COMMENT_REPLIED
        )

    def notify_mentioned_users(self, comment):
        if comment.revisions.count() > 0:
            rev_comment = comment.revisions.latest('created')
            self._remove_by_unmentioned_users(comment)
        user_qs = comment.mentioned_users.exclude(pk=comment.user.pk)
        for user in user_qs.all():
            self.create(
                sender=comment.user,
                receiver=user,
                comment=comment,
                notif_type=Notification.USER_MENTIONED
            )

    def _remove_by_unmentioned_users(self, comment):
        for user in comment.mentioned_users.all():
            queryset = self.filter(
                sender=comment.user,
                receiver=user,
                comment=comment,
                notif_type=Notification.USER_MENTIONED
            )
            if queryset.exists():
                queryset.first().delete()

    def notify_user_followers_for_thread_creation(self, thread):
        for user in thread.user.followers.all():
            self.create(
                sender=thread.user,
                receiver=user,
                thread=thread,
                notif_type=Notification.THREAD_CREATED
            )

    def notify_thread_followers_for_modification(self, thread):
        other_followers = thread.followers.exclude(
            threadfollowership__user=thread.user
        )
        for user in other_followers.all():
            self.get_or_create(
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
        )
        if queryset.exists():
            queryset.first().delete()

    def mark_as_read(self, receiver, notif_id_list):
        # Be aware that the update() method is converted directly
        # to an SQL statement. It is a bulk operation for direct updates.
        # It doesn’t run any save() methods on your models,
        # or emit the pre_save or post_save signals (which are a consequence
        # of calling save()), or honor the auto_now field option.
        # https://docs.djangoproject.com/en/1.11/topics/db/queries/#updating-multiple-objects-at-once
        self.get_for_user(
            receiver
        ).filter(unread=True, id__in=notif_id_list).update(
            unread=False, modified=timezone.now()
        )

    def get_receiver_url_and_count(self, receiver):
        qs_receiver = self.get_for_user(receiver)
        unread_qs = qs_receiver.filter(
            unread=True
        ).order_by('-created')
        position = 0
        url = ''
        if unread_qs.exists() and unread_qs.first():
            for model in qs_receiver.all():
                position = position + 1
                if model.pk == unread_qs.first().pk:
                    break
            if position:
                page_num = ceil(position / 3)
                url = '%s?page=%s' % (
                    reverse(
                        'accounts:user_notifs',
                        kwargs={'username': receiver.username}
                    ),
                    page_num
                )
        if not url:
            url = reverse(
                'accounts:user_notifs', kwargs={'username': receiver.username}
            )
        count = unread_qs.count()
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
        "threads.Thread", on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(
        "comments.Comment", on_delete=models.CASCADE, null=True, blank=True)
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

    def get_precise_url(self):
        notif_qs = Notification.objects.filter(receiver=self.receiver)
        position = 0
        for notif in notif_qs:
            position = position + 1
            if notif.pk == self.pk:
                break
        page_num = ceil(position / 3)
        return '%s?page=%s' % (reverse('accounts:user_notifs', kwargs={'username': self.receiver}), page_num)
