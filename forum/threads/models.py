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
from forum.threads.managers import ThreadQuerySet


class Thread(TimeStampedModel):
    title = models.CharField(max_length=150)
    slug = models.SlugField(blank=True, max_length=255)
    body = models.TextField(max_length=4000)
    category = models.ForeignKey(
        "categories.Category", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    likes = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    visible = models.BooleanField(default=True)
    followers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ThreadFollowership', related_name='thread_following'
    )
    # reader = models.ManyToManyField(
    #     settings.AUTH_USER_MODEL,
    #     through='threads.ThreadActivity', related_name='thread_activity'
    # )
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
            ThreadFollowership.objects.create_followership(self.user, self)
            Notification.objects.notify_user_followers_for_thread_creation(
                self
            )
        else:
            old_thread = None
            if Thread.objects.filter(pk=self.pk).exists():
                old_thread = Thread.objects.filter(pk=self.pk).first()
            # There cannot be revision for a thread without a starting comment
            if old_thread and old_thread.starting_comment:
                # There cannot be revision when a thread comment count is being
                # incremented (an F expression is used for increasing comment count,
                # the instance of comment count can be used to perform this check.)
                if isinstance(self.comment_count, int):
                    ThreadRevision.objects.create(
                        thread=old_thread,
                        starting_comment=old_thread.starting_comment,
                        title=old_thread.title,
                        message=old_thread.starting_comment.message,
                        marked_message=old_thread.starting_comment.marked_message
                    )
                    # Notify for modification only when there is a reply
                    if self.comment_count:
                        Notification.objects.notify_thread_followers_for_modification(
                            self
                        )
            super(Thread, self).save(*args, **kwargs)

    def sync_with_comment(self, final_user, final_time):
        self.final_comment_user = final_user
        self.final_comment_time = final_time
        self.comment_count = F('comment_count') + 1
        print("sync_with_comment called")
        self.save()
        # To prevent thread comment count from incrementing twice
        # by ensuring that comment_count value is tied to the thread rather
        # than the F expression which was used for the increment.
        self.refresh_from_db()

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
            user=comment.user, thread=comment.thread
        ).update(comment_time=comment.created, final_comment=comment)

        thread_fship_qs = comment.thread.threadfollowership_set.exclude(
            user=comment.user
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

    def create_followership(self, user, thread):
        ''' 
        Use to create thread followership when a user creates
        a new thread or new comment. It is called through the
        model's save() method which is used for both updating
        the thread.
        '''
        # for comment in Comment.objects.get_for_thread(thread):
        #     CommentActivity.objects.create(
        #         user=user, thread=thread, comment=comment, unread=False
        #     )
        now = timezone.now()
        thread_fship_qs = self.filter(
            user=user, thread=thread
        )
        if not thread_fship_qs.exists():
            self.create(
                user=user, thread=thread, comment_time=now
            )

    def toggle_thread_followership(self, user, thread, comment_time):
        queryset = self.filter(
            user=user, thread=thread
        )
        if queryset.exists():
            queryset.first().delete()
        else:
            now = comment_time
            if not now:
                now = timezone.now
            self.create(
                user=user, thread=thread, comment_time=now
            )

    def get_related(self):
        return self.select_related(
            'user', 'thread', 'final_comment'
        )
        # .prefetch_related(
        #     'userprofile__user'
        # )


class ThreadFollowership(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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
            self.user.username,
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


# class ThreadActivityQuerySet(models.query.QuerySet):

#     def mark_as_read(self, user, thread, comment_id_list, url):
#         # Be aware that the update() method is converted directly
#         # to an SQL statement. It is a bulk operation for direct updates.
#         # It doesn’t run any save() methods on your models,
#         # or emit the pre_save or post_save signals (which are a consequence
#         # of calling save()), or honor the auto_now field option.
#         # https://docs.djangoproject.com/en/1.11/topics/db/queries/#updating-multiple-objects-at-once
#         self.get_for_user(
#             user
#         ).filter(unread=True, thread=thread, id__in=comment_id_list).update(
#             unread=False, first_comment_url=url, modified=timezone.now()
#         )

#     def get_unread_url_and_count(self, user, thread):
#         qs_user = self.get_for_user(user)
#         unread_qs = qs_user.filter(comment__thread=thread, unread=True)
#         position = 0
#         first_unread_comment = None
#         if unread_qs.exists() and unread_qs.first():
#             for comment in Comment.objects.get_for_thread(thread):
#                 position = position + 1
#                 if comment.pk == unread_qs.first().pk:
#                     first_unread_comment = comment
#                     break
#         url = ''
#         if unread_qs.exists() and first_unread_comment:
#             page_num = ceil(position / COMMENT_PER_PAGE)
#             url = '%s?page=%s&read=True#comment%s' % (
#                 thread.get_absolute_url(), str(page_num), str(first_unread_comment.pk)
#             )
#         else:
#             url = thread.get_absolute_url()
#         count = unread_qs.count()
#         return url, count

#     def get_for_user(self, user):
#         return self.filter(user=user)


# class ThreadActivity(TimeStampedModel):
#     comment = models.ForeignKey('comments.Comment', on_delete=models.CASCADE)
#     thread = models.ForeignKey('threads.Thread', on_delete=models.CASCADE)
#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL, on_delete=models.CASCADE
#     )
#     unread = models.BooleanField(default=False)
#     first_comment_url = models.CharField(blank=True, null=True)
#     objects = ThreadActivityQuerySet.as_manager()
