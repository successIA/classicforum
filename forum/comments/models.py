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
from forum.image_app.models import Image
from forum.core.bbcode_quote import bbcode_quote
from forum.core.constants import COMMENT_PER_PAGE
from forum.core.utils import convert_mention_to_link

from markdown import markdown
import bleach
from bleach_whitelist import markdown_tags, markdown_attrs


class CommentQuerySet(models.query.QuerySet):

    def get_new_for_user(self, user, thread, time):
        if not user.is_authenticated:
            return
        if not time:
            return 
        queryset = self.filter(thread=thread, created__gt=time)
        return queryset.exclude(user=user)

    def get_for_thread(self, thread):
        queryset = self.active().get_related().filter(thread=thread)
        return queryset.order_by('created').all()

    def get_user_last_posted(self, user):
        queryset = self.filter(user=user)
        if queryset.count() > 0:
            return queryset.latest('created').created

    def get_user_active_category(self, user):
        if user.comment_set.count() > 0:
            return self.values('thread').filter(
                user=user
            ).annotate(category=F('thread__category__title')).annotate(
                thread_count=Count('thread')
            ).order_by('-thread_count')[0].get('category')

    def get_recent_for_user(self, user, count):
        return self.get_related().filter(
            user=user
        ).exclude(is_starting_comment=True).order_by('-created')[:count]

    def get_user_total_upvotes(self, user):
        queryset = self.filter(user=user).annotate(upvotes=Count('upvoters'))
        total_upvotes = 0
        for model_instance in queryset:
            total_upvotes = total_upvotes + model_instance.upvotes
        return total_upvotes

    def get_related(self):
        return self.select_related(
            'thread', 'user', 'parent'
        ).prefetch_related(
            # 'attachment_set',
            'user__userprofile__attachment_set',
            'revisions', 
            'user__userprofile', 
            'parent__user',
            'parent__thread',
            'upvoters',
            'downvoters'
        )

    def get_parent(self, pk):
        comment_qs = None
        try:
            comment_qs = self.filter(pk=int(pk))
        except:
            return None
        if comment_qs.exists():
            return comment_qs.first()

    def active(self, *args, **kwargs):
        return self.filter(visible=True)


class Comment(TimeStampedModel):
    message = models.TextField(max_length=4000)
    marked_message =  models.TextField(max_length=4000, blank=True)
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
        related_name = 'comment_mention'
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
        if user in self.downvoters.all():
            self.downvoters.remove(user)
        else:
            self.upvoters.remove(user)
            self.downvoters.add(user)  

    def upvote(self, user):
        from forum.notifications.utils import (
            delete_comment_upvote_notif
        )
        from forum.notifications.models import Notification

        if user in self.upvoters.all():
            self.upvoters.remove(user)
            delete_comment_upvote_notif(user, self)
        else:
            self.downvoters.remove(user)
            self.upvoters.add(user)
            Notification.objects.create(
                sender=user, 
                receiver=self.user,
                comment=self, 
                notif_type=Notification.COMMENT_UPVOTED
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
        related_name = 'comment_rev_mention'
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






