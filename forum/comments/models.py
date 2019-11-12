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

from forum.core.models import TimeStampedModel
from forum.core.bbcode_quote import bbcode_quote
from forum.core.constants import COMMENT_PER_PAGE
from forum.core.utils import convert_mention_to_link
from forum.comments.managers import CommentQuerySet

from markdown import markdown
import bleach
from bleach_whitelist import markdown_tags, markdown_attrs


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
        settings.AUTH_USER_MODEL, related_name='upvoted_comments'
    )
    downvoters = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='downvoted_comments'
    )
    # voters = models.ManyToManyField(
    #     settings.AUTH_USER_MODEL,
    #     related_name='voted_comments',
    #     through=CommentVote
    # )
    position = models.IntegerField(default=0)
    visible = models.BooleanField(default=True)
    objects = CommentQuerySet.as_manager()

    def save(self, *args, **kwargs):
        from forum.attachments.models import Attachment
        from forum.threads.models import ThreadFollowership
        from forum.notifications.models import Notification
        from forum.comments.utils import get_mentioned_users

        message = bleach.clean(self.message, markdown_tags, markdown_attrs)
        if not self.pk:
            if self.is_starting_comment:
                self.position = 0
            else:
                self.position = self.thread.comments.count() + 1
            super(Comment, self).save(*args, **kwargs)
            if not self.is_starting_comment:
                self.thread.sync_with_comment(self.user, self.created)
            Attachment.objects.sync_with_comment(self)
            ThreadFollowership.objects.create_followership(
                self.user, self.thread
            )
            ThreadFollowership.objects.sync_with_comment(self)
            if self.parent and self.parent.user != self.user:
                Notification.objects.notify_receiver_for_reply(self)
        else:
            comment_revision = CommentRevision(
                comment=self,
                message=self.message,
                marked_message=self.marked_message
            )
            comment_revision.save()
            comment_revision.mentioned_users = self.mentioned_users.all()
            comment_revision.save()
            Attachment.objects.sync_with_comment(self, comment_revision)
            super(Comment, self).save(*args, **kwargs)
        self.mentioned_users = get_mentioned_users(self.message)
        self.marked_message = self.get_rendered_message()
        # To prevent integrity constraint violation
        kwargs["force_update"] = True
        # To prevent integrity constraint violation
        kwargs["force_insert"] = False
        super(Comment, self).save(*args, **kwargs)
        Notification.objects.notify_mentioned_users(self)

    def __str__(self):
        return self.message[:32]

    def get_rendered_message(self):
        message = convert_mention_to_link(self.message, self.mentioned_users)
        text, comment_info_list = bbcode_quote(message)
        text = markdown(text, safe_mode='escape')
        return mark_safe(text)

    def is_owner(self, user):
        return self.user == user

    def get_precise_url(self, page_num=None):
        if not page_num:
            count = self.position
            page_num = ceil(count / COMMENT_PER_PAGE)
        return '%s?page=%s&read=True#comment%s' % (
            self.thread.get_absolute_url(), str(page_num), str(self.pk)
        )

    def get_reply_url(self):
        return '%scomments/%s/reply/' % (
            self.thread.get_absolute_url(), str(self.pk)
        )

    def get_update_url(self):
        return '%scomments/%s/' % (
            self.thread.get_absolute_url(), str(self.pk)
        )

    def get_form_reply_url(self, page_num):
        return '%scomments/%s/reply/?page=%s#comment-form' % (
            self.thread.get_absolute_url(), str(self.pk), str(page_num)
        )

    def get_reply_form_action(self):
        page_num = ceil(self.position / 5)
        return self.get_form_reply_url(page_num)

    def get_form_update_url(self, page_num):
        return '%scomments/%s/?page=%s#comment-form' % (
            self.thread.get_absolute_url(), str(self.pk), str(page_num)
        )

    def get_update_form_action(self):
        page_num = ceil(self.position / 5)
        return self.get_form_update_url(page_num)

    def get_upvote_url(self):
        return '%scomments/%s/upvote/' % (
            self.thread.get_absolute_url(), str(self.pk)
        )

    def get_downvote_url(self):
        return '%scomments/%s/downvote/' % (
            self.thread.get_absolute_url(), str(self.pk)
        )

    def downvote(self, user):
        from forum.notifications.models import Notification

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
        from forum.notifications.models import Notification

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

    def __str__(self):
        return 'Comment History-%s' % (self.created)

    def get_message_as_markdown(self):
        from markdown import markdown
        text, comment_info_list = bbcode_quote(self.message)
        return mark_safe(markdown(text, safe_mode='escape'))




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
