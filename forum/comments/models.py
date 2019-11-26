import random
import string
from math import ceil

from django.db.models import Max, Min, Count, F, Value, CharField, Prefetch
from django.shortcuts import get_object_or_404
from django.db import models
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models.signals import pre_save
from django.utils.text import slugify
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.html import mark_safe
from django.http import (
    HttpResponse, HttpResponseRedirect, Http404, HttpResponseForbidden
)

from markdown import markdown
import bleach
from bleach_whitelist import markdown_tags, markdown_attrs

from forum.core.models import TimeStampedModel
from forum.core.constants import COMMENT_PER_PAGE
from forum.comments.managers import CommentQuerySet
from forum.attachments.models import Attachment
from forum.threads.models import ThreadFollowership
from forum.notifications.models import Notification
from forum.accounts.models import User
from forum.core.utils import find_mentioned_usernames
from forum.threads.tasks import (
    sync_attachment_with_comment,
    sync_comment_with_thread_followership
)


class Comment(TimeStampedModel):
    message = models.TextField(max_length=4000)
    marked_message = models.TextField(max_length=4000, blank=True)
    thread = models.ForeignKey(
        'threads.Thread', on_delete=models.CASCADE, related_name='comments'
    )
    is_starting_comment = models.BooleanField(default=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    parent = models.ForeignKey('self', blank=True, null=True)
    mentioned_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='comment_mention'
    )
    upvoters = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='upvoted_comments'
    )
    downvoters = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='downvoted_comments'
    )
    # voters = models.ManyToManyField(
    #     settings.AUTH_USER_MODEL,
    #     related_name='voted_comments',
    #     through=CommentVote
    # )
    position = models.IntegerField(default=0)
    offset = models.IntegerField(default=0)
    visible = models.BooleanField(default=True)
    objects = CommentQuerySet.as_manager()

    def delete(self, *args, **kwargs):
        self.thread.comments.filter(pk__gt=self.pk).update(
            offset=F('offset') - 1
        )
        super(Comment, self).delete(*args, **kwargs)
        instance = self.thread.comments.last()
        self.thread.sync_with_comment(instance, is_create=False)

    def save(self, *args, **kwargs):
        from forum.comments.utils import get_rendered_message

        new_instance = False
        if self.pk:
            prev_instance = self.__class__.objects.filter(pk=self.pk).first()
            if prev_instance:
                CommentRevision.objects.create_from_comment(prev_instance)
                self.mentioned_users.clear()
        else:
            new_instance = True
            if not self.is_starting_comment:
                self.position = self.thread.comment_count + 1

        self.message = bleach.clean(
            self.message, markdown_tags, markdown_attrs
        )
        mentions = find_mentioned_usernames(self.message)
        mentioned_user_list = list(
            User.objects.filter(username__in=mentions).all()
        )
        user_value_list = [{'username': usr.username, 'url': usr.get_absolute_url()}
                           for usr in mentioned_user_list]
        self.marked_message = get_rendered_message(
            self.message, user_value_list
        )
        super(Comment, self).save(*args, **kwargs)

        if new_instance:
            sync_attachment_with_comment(self.pk)
            if not self.is_starting_comment:
                self.thread.sync_with_comment(self)
                # sync_comment_with_thread_followership(self.thread.pk, self.pk)
                ThreadFollowership.objects.sync_with_comment(
                    self.thread, self
                )
            if self.parent and self.parent.user != self.user:
                Notification.objects.notify_receiver_for_reply(self)
        self.mentioned_users.add(*mentioned_user_list)
        Notification.objects.notify_mentioned_users(self, mentioned_user_list)

    def __str__(self):
        return self.message[:32]

    def is_owner(self, user):
        return self.user == user

    def downvote(self, user):
        if user in self.downvoters.all():
            self.downvoters.remove(user)
        else:
            self.upvoters.remove(user)
            self.downvoters.add(user)
            # Incase the user upvoted the comment initially by mistake
            Notification.objects.delete_comment_upvote_notification(
                user, self.user, self
            )

    def upvote(self, user):
        if user in self.upvoters.all():
            self.upvoters.remove(user)
            Notification.objects.delete_comment_upvote_notification(
                user, self.user, self
            )
        else:
            self.downvoters.remove(user)
            self.upvoters.add(user)
            Notification.objects.notify_receiver_for_comment_upvote(
                user, self.user, self
            )

    def get_precise_url(self, page_num=None):
        if not page_num:
            count = self.position - self.offset
            page_num = ceil(count / COMMENT_PER_PAGE)
        return '%s?page=%s&read=True#comment%s' % (
            self.thread.get_absolute_url(), page_num, self.pk
        )

    def get_reply_url(self):
        return reverse(
            'comments:comment_reply',
            kwargs={'thread_slug': self.thread.slug, 'pk': self.pk}
        )

    def get_update_url(self):
        return reverse(
            'comments:comment_update',
            kwargs={'thread_slug': self.thread.slug, 'pk': self.pk}
        )

    def get_upvote_url(self):
        return reverse(
            'comments:upvote',
            kwargs={'thread_slug': self.thread.slug, 'pk': self.pk}
        )

    def get_downvote_url(self):
        return reverse(
            'comments:downvote',
            kwargs={'thread_slug': self.thread.slug, 'pk': self.pk}
        )

    def get_reply_form_action(self):
        page_num = ceil(self.position / COMMENT_PER_PAGE)
        return '%s?page=%s#comment-form' % (
            reverse(
                'comments:comment_reply',
                kwargs={'thread_slug': self.thread.slug, 'pk': self.pk}
            ),
            page_num
        )

    def get_update_form_action(self):
        page_num = ceil(self.position / COMMENT_PER_PAGE)
        return '%s?page=%s#comment-form' % (
            reverse(
                'comments:comment_update',
                kwargs={'thread_slug': self.thread.slug, 'pk': self.pk}
            ),
            page_num
        )


class CommentRevisionQuerySet(models.query.QuerySet):
    def create_from_comment(self, comment):
        instance = self.create(
            comment=comment,
            message=comment.message,
            marked_message=comment.marked_message
        )
        mentioned_users = comment.mentioned_users.all()
        instance.mentioned_users.add(*mentioned_users)
        # Attachment.objects.sync_with_comment(comment, instance.message)
        sync_attachment_with_comment(comment.pk, message=instance.message)


class CommentRevision(models.Model):
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name="revisions"
    )
    message = models.TextField(max_length=4000)
    marked_message = models.TextField(max_length=4000, blank=True)
    mentioned_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='comment_rev_mention'
    )
    created = models.DateTimeField(auto_now_add=True)
    objects = CommentRevisionQuerySet.as_manager()

    def __str__(self):
        return 'Comment History-%s' % (self.created)

    # def get_message_as_markdown(self):
    #     from markdown import markdown
    #     text, comment_info_list = bbcode_quote(self.message)
    #     return mark_safe(markdown(text, safe_mode='escape'))


# from forum.threads.models import Thread
# for thread in Thread.objects.all():
#      starting_comment = thread.starting_comment
#      starting_comment.user = thread.user
#      starting_comment.save()


# class CommentVoteQuerySet(models.query.QuerySet):

#     def upvote(self, comment, voter):
#         from forum.notifications.models import Notification

#         queryset = self.filter(comment=comment, voter=voter)
#         if queryset.exists():
#             queryset.first().delete()
#             notif_qs = Notification.objects.filter(
#                 sender=voter,
#                 receiver=comment.user,
#                 comment=comment,
#                 notif_type=Notification.COMMENT_UPVOTED
#             )
#             if notif_qs.exists():
#                 notif_qs.first().delete()

#         else:
#             self.create(comment=comment, voter=voter, vote=CommentVote.UPVOTE)
#             Notification.objects.create(
#                 sender=voter,
#                 receiver=comment.user,
#                 comment=comment,
#                 notif_type=Notification.COMMENT_UPVOTED
#             )

#     def downvote(self, comment, voter):
#         queryset = self.filter(comment=comment, voter=voter)
#         if queryset.exists():
#             queryset.first().delete()
#         else:
#             self.create(comment=comment, voter=voter, vote=CommentVote.DOWNVOTE)


# class CommentVote(TimeStampedModel):
#     UPVOTE = 'u'
#     DOWNVOTE = 'd'
#     VOTE_CHOICES = (
#         (UPVOTE, 'upvote'),
#         (DOWNVOTE, 'downvote')
#     )
#     comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
#     voter = models.ForeignKey(
#         settings.AUTH_USER_MODEL, on_delete=models.CASCADE
#     )
#     vote = models.CharField(max_length=1, choices=VOTE_CHOICES)
#     objects = CommentVoteQuerySet.as_manager()
