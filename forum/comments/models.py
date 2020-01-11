import random
import string
from math import ceil

from django.db.models import Max, Min, Count, F, Value, CharField, Prefetch
from django.shortcuts import get_object_or_404
from django.db import models, transaction
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
from forum.accounts.utils import get_user_list_without_creator


class Comment(TimeStampedModel):
    message = models.TextField(max_length=4000)
    marked_message = models.TextField(max_length=4000, blank=True)
    category = models.ForeignKey(
        'categories.Category', on_delete=models.CASCADE, related_name='comments'
    )
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

    def __str__(self):
        return self.message[:32]

    def set_position(self):
        self.position = self.thread.comment_count + 1

    def set_message(self):
        from forum.comments.utils import (
            get_rendered_message,
            get_mentioned_users_in_message,
            get_user_value_list,
        )
        self.message = bleach.clean(self.message)
        mentioned_users = get_mentioned_users_in_message(self.message)
        user_value_list = get_user_value_list(mentioned_users)
        self.marked_message = get_rendered_message(
            self.message, user_value_list
        )
        return mentioned_users

    def save(self, *args, **kwargs):
        if not self.pk:
            self.category = self.thread.category
        super(Comment, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.hide()
        # self.thread.comments.filter(pk__gt=self.pk).update(
        #     offset=F('offset') - 1
        # )
        super(Comment, self).delete(*args, **kwargs)
        # instance = self.thread.comments.last()
        # self.thread.sync_with_comment(instance, is_create=False)
    
    def hide(self, *args, **kwargs):
        self.thread.comments.pure().filter(
            pk__gt=self.pk
        ).update(
            offset=F('offset') - 1
        )

        self.thread.comments.pure().filter(
            pk=self.pk
        ).update(visible=False)

        self.thread.synchronise(self._get_last(), added=False)
    
    def unhide(self, *args, **kwargs):
        self.thread.comments.pure().filter(
            pk__gt=self.pk
        ).update(
            offset=F('offset') + 1
        )

        self.thread.comments.pure().filter(
            pk=self.pk
        ).update(visible=True)
        
        self.thread.synchronise(self._get_last())
    
    def _get_last(self):
        last_obj = None
        last_obj_qs = self.thread.comments.pure_and_active()
        if last_obj_qs:
            last_obj = last_obj_qs.last()
        return last_obj

    @transaction.atomic
    def downvote(self, user):
        if user in self.downvoters.all():
            self.downvoters.remove(user)
        else:
            self.upvoters.remove(user)
            self.downvoters.add(user)
            # Incase the user upvoted the comment initially by mistake
            Notification.objects.filter(
                sender=user, receiver=self.user,
                comment=self, notif_type=Notification.COMMENT_UPVOTED
            ).delete()

    @transaction.atomic
    def upvote(self, user):
        if user in self.upvoters.all():
            self.upvoters.remove(user)
            Notification.objects.filter(
                sender=user, receiver=self.user,
                comment=self, notif_type=Notification.COMMENT_UPVOTED
            ).delete()
        else:
            self.downvoters.remove(user)
            self.upvoters.add(user)
            Notification.objects.create(
                sender=user, receiver=self.user,
                comment=self, notif_type=Notification.COMMENT_UPVOTED
            )
    
    def is_owner(self, user):
        return self.user == user

    @property
    def index(self):
        return self.position + self.offset

    def get_precise_url(self, page_num=None):
        if not page_num:
            count = self.position + self.offset
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

    def get_url_for_next_or_prev(self):
        if self.position > 1:
            next_obj_qs = self.__class__.objects.active().filter(
                pk__gt=self.pk
            ).order_by('pk')
            if next_obj_qs:
                return next_obj_qs.first().get_precise_url()
            else:
                prev_obj_qs = self.__class__.objects.active().filter(
                    pk__lt=self.pk
                ).order_by('pk')
                if prev_obj_qs:
                    return prev_obj_qs.last().get_precise_url()    
        return self.thread.get_absolute_url()


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
