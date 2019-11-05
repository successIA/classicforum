from django.shortcuts import get_object_or_404
from django.db import models, connection
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models.signals import pre_save
from django.utils.text import slugify
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.html import mark_safe
from django.utils import timezone
from django.db.models import Max, Min, Count, F, Value, CharField, Prefetch


from forum.core.models import TimeStampedModel
from forum.core.bbcode_quote import bbcode_quote
from forum.categories.models import Category
from forum.accounts.models import UserProfile
from forum.threads.managers import ThreadQuerySet


class Thread(TimeStampedModel):
    title = models.CharField(max_length=150)
    slug = models.SlugField(blank=True, max_length=255)
    body = models.TextField(max_length=4000)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    userprofile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    likes = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    visible = models.BooleanField(default=True)
    followers = models.ManyToManyField(
        UserProfile,
        through='ThreadFollowership', related_name='thread_following'
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
        from forum.threads.utils import create_thread_slug
        from forum.notifications.models import Notification
        if not self.pk:
            self.slug = create_thread_slug(self)
            super(Thread, self).save(*args, **kwargs)
            ThreadFollowership.objects.create_followership(
                self.user.userprofile, self
            )
            Notification.objects.notify_user_followers_for_thread_creation(
                self
            )
        else:
            # Create thread revision when the thread is fully created
            # with starting comment. A thread can only have a starting
            # comment after it is saved to the db.
            if self.starting_comment:
                ThreadRevision.objects.create(
                    thread=self,
                    starting_comment=self.starting_comment,
                    title=self.title,
                    message=self.starting_comment.message,
                    marked_message=self.starting_comment.marked_message
                )
            super(Thread, self).save(*args, **kwargs)
            Notification.objects.notify_thread_followers_for_modification(
                self
            )

    def sync_with_comment(self, final_user, final_time):
        self.final_comment_user = final_user
        self.final_comment_time = final_time
        self.comment_count = F('comment_count') + 1
        self.save()

    def get_absolute_url(self):
        return reverse('thread_detail', kwargs={'thread_slug': self.slug})

    def get_precise_url(self, page_num):
        return '%sedit/?page=%s' % (
            self.get_absolute_url(), str(page_num)
        )

    def is_owner(self, user):
        return self.user == user

    def get_thread_update_url(self):
        return reverse('thread_update', kwargs={'thread_slug': self.slug})

    def get_thread_follow_url(self):
        return reverse('thread_follow', kwargs={'thread_slug': self.slug})

    def get_comment_create_url(self):
        return reverse('comment_create', kwargs={'thread_slug': self.slug})

    def get_comment_create_url2(self, page_num):
        return '%scomments/add/?page=%s#comment-form' % (
            self.get_absolute_url(), str(page_num)
        )


class ThreadFollowershipQuerySet(models.query.QuerySet):
    def sync_with_comment(self, comment):
        self.filter(
            userprofile=comment.user.userprofile, thread=comment.thread
        ).update(comment_time=comment.created, final_comment=comment)

        thread_fship_qs = comment.thread.threadfollowership_set.exclude(
            userprofile=comment.user.userprofile
        )
        for tf in thread_fship_qs:
            tf.new_comment_count = F('new_comment_count') + 1
            tf.save()
            tf.refresh_from_db()
            # Update only the final_comment and has_new_comment of followers
            # whom are yet to see any new comment
            if not tf.has_new_comment:
                tf.final_comment = comment
                tf.has_new_comment = True
                tf.save()

    def create_followership(self, userprofile, thread):
        ''' 
        Use to create thread followership when a user creates
        a new thread or new comment. It is called through the
        model's save() method which is used for both updating
        the thread.
        '''
        now = timezone.now()
        thread_fship_qs = self.filter(
            userprofile=userprofile, thread=thread
        )
        if not thread_fship_qs.exists():
            self.create(
                userprofile=userprofile, thread=thread, comment_time=now
            )

    def toggle_thread_followership(self, userprofile, thread, comment_time):
        queryset = self.filter(
            userprofile=userprofile, thread=thread
        )
        if queryset.exists():
            queryset.first().delete()
        else:
            now = comment_time
            if not now:
                now = timezone.now
            self.create(
                userprofile=userprofile, thread=thread, comment_time=now
            )

    def get_related(self):
        return self.select_related(
            'userprofile', 'thread', 'final_comment'
        ).prefetch_related(
            'userprofile__user'
        )


class ThreadFollowership(TimeStampedModel):
    userprofile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    thread = models.ForeignKey('Thread', on_delete=models.CASCADE)
    comment_time = models.DateTimeField()  # time of the most recent comment
    final_comment = models.ForeignKey(
        'comments.Comment', on_delete=models.SET_NULL, null=True, blank=True
    )
    new_comment_count = models.PositiveIntegerField(default=0)
    has_new_comment = models.BooleanField(default=False)
    objects = ThreadFollowershipQuerySet.as_manager()

    def __str__(self):
        return '%s_%s_%s' % (
            self.userprofile.user.username,
            ''.join(list(self.thread.slug)[:32]),
            str(self.thread.id)
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

    def __str__(self):
        return 'Thread History-%s' % (self.created)

    def get_message_as_markdown(self):
        from markdown import markdown
        text, comment_info_list = bbcode_quote(self.message)
        return mark_safe(markdown(text, safe_mode='escape'))
