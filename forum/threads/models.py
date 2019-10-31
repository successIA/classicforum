from django.shortcuts import get_object_or_404
from django.db import models, connection
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models.signals import pre_save
from django.utils.text import slugify
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.html import mark_safe

from forum.core.models import TimeStampedModel
from forum.core.bbcode_quote import bbcode_quote
from forum.categories.models import Category
from forum.accounts.models import UserProfile
from forum.image_app.models import Image
from forum.threads.managers import ThreadQuerySet


class Thread(TimeStampedModel):
    title = models.CharField(max_length=150)
    slug = models.SlugField(blank=True, max_length=255)
    body = models.TextField(max_length=4000)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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
    def get_related(self):
        return self.select_related(
            'userprofile', 'thread', 'final_comment'
        ).prefetch_related(
            'userprofile__user'
        )

class ThreadFollowership(TimeStampedModel):
    userprofile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    thread = models.ForeignKey('Thread', on_delete=models.CASCADE)
    comment_time = models.DateTimeField() # time of the most recent comment
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


