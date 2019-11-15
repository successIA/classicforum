from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import CharField, Count, F, Max, Min, Prefetch, Value
from django.utils.html import mark_safe
from django.utils.text import slugify

from forum.categories.models import Category
from forum.core.bbcode_quote import bbcode_quote
from forum.core.models import TimeStampedModel
from forum.threads.managers import ThreadQuerySet
from forum.notifications.models import Notification
from forum.core.utils import find_mentioned_usernames


class Thread(TimeStampedModel):
    title = models.CharField(max_length=150)
    slug = models.SlugField(blank=True, max_length=255)
    body = models.TextField(max_length=4000)
    category = models.ForeignKey(
        'categories.Category', on_delete=models.CASCADE
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    likes = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    visible = models.BooleanField(default=True)
    followers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='thread_following'
    )
    readers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='threads.ThreadActivity', related_name='thread_activity'
    )
    starting_comment = models.ForeignKey(
        'comments.Comment', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='starting_thread'
    )
    final_comment_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        blank=True, null=True, related_name='final_thread'
    )
    final_comment_time = models.DateTimeField(null=True, blank=True)
    comment_count = models.PositiveIntegerField(default=0)
    objects = ThreadQuerySet.as_manager()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk:
            self.slug = self.__class__.objects.generate_slug(self)
            super(Thread, self).save(*args, **kwargs)
            self.followers.add(self.user)
            Notification.objects.notify_user_followers_for_thread_creation(
                self
            )
        else:
            prev_instance = self.__class__.objects.filter(pk=self.pk).first()
            if prev_instance:
                ThreadRevision.objects.create_from_thread(prev_instance)
            super(Thread, self).save(*args, **kwargs)
            Notification.objects.notify_thread_followers_for_modification(self)

    def sync_with_comment(self, comment, is_create=True):
        if is_create:
            self.__class__.objects.filter(pk=self.pk).update(
                final_comment_user=comment.user,
                final_comment_time=comment.created,
                comment_count=F('comment_count') + 1
            )
        else:
            if self.comment_count > 0:
                self.__class__.objects.filter(pk=self.pk).update(
                    final_comment_user=comment.user,
                    final_comment_time=comment.created,
                    comment_count=F('comment_count') - 1
                )

    def toggle_follower(self, follower):
        if follower not in self.followers.all():
            self.followers.add(follower)
        else:
            self.followers.remove(follower)

    def is_owner(self, user):
        return self.user == user

    def get_absolute_url(self):
        return reverse('thread_detail', kwargs={'thread_slug': self.slug})

    def get_update_url(self):
        return "%sedit/" % (self.get_absolute_url())

    def get_thread_update_form_action(self):
        return "%s" % (
            reverse('thread_update', kwargs={'thread_slug': self.slug})
        )

    def get_comment_create_form_action(self, page_num):
        return '%scomments/add/?page=%s#comment-form' % (
            self.get_absolute_url(), str(page_num)
        )

    def get_thread_follow_url(self):
        return reverse('thread_follow', kwargs={'thread_slug': self.slug})


class ThreadRevisionQuerySet(models.query.QuerySet):
    def create_from_thread(self, thread):
        self.create(
            thread=thread,
            starting_comment=thread.starting_comment,
            title=thread.title,
            message=thread.starting_comment.message,
            marked_message=thread.starting_comment.marked_message
        )


class ThreadRevision(models.Model):
    thread = models.ForeignKey(
        Thread, on_delete=models.CASCADE, related_name="revisions"
    )
    starting_comment = models.ForeignKey(
        'comments.Comment', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='starting_thread_revision'
    )
    title = models.TextField()
    message = models.TextField()
    marked_message = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    objects = ThreadRevisionQuerySet.as_manager()

    def __str__(self):
        return 'Thread History-%s' % (self.created)


class ThreadActivityQuerySet(models.query.QuerySet):
    def create_activities(self, thread, comment):
        users = [usr for usr in thread.followers.all()
                 if usr.pk != comment.user.pk]
        activities = []
        for user in users:
            activities.append(
                self.model(
                    user=user, thread=thread, comment=comment
                )
            )
        self.bulk_create(activities)

    def update_activity_actions(self, user, thread, comments):
        queryset = self.filter(
            user=user, thread=thread
        ).select_related('comment')

        comment_pk_list = []
        for comment in comments:
            for model in queryset:
                if comment.pk == model.comment.pk:
                    comment.unread = True
                    comment_pk_list.append(comment.pk)
        if comment_pk_list:
            self.filter(
                user=user, thread=thread, comment__in=comment_pk_list
            ).delete()


class ThreadActivity(TimeStampedModel):
    comment = models.ForeignKey('comments.Comment', on_delete=models.CASCADE)
    thread = models.ForeignKey('threads.Thread', on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    objects = ThreadActivityQuerySet.as_manager()

    # def __str__(self):
    #     return "%s - %s - %s" % (self.user.username, self.thread.title[:30], self.comment.id)
