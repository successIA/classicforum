from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import CharField, Count, F, Max, Min, Prefetch, Value
from django.utils.html import mark_safe
from django.utils.text import slugify

from forum.categories.models import Category
from forum.core.bbcode_quote import bbcode_quote
from forum.core.models import TimeStampedModel
from forum.core.constants import COMMENT_PER_PAGE
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
        settings.AUTH_USER_MODEL,
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
        if not self.pk:
            self.slug = self.__class__.objects.generate_slug(self)
            super(Thread, self).save(*args, **kwargs)
            # self.followers.add(self.user)
            ThreadFollowership.objects.get_or_create(
                user=self.user, thread=self
            )
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
        elif self.comment_count > 0:
                self.__class__.objects.filter(pk=self.pk).update(
                    final_comment_user=comment.user,
                    final_comment_time=comment.created,
                    comment_count=F('comment_count') - 1
            )

    # def toggle_follower(self, follower):
    #     if follower not in self.followers.all():
    #         self.followers.add(follower)
    #     else:
    #         self.followers.remove(follower)

    def is_owner(self, user):
        return self.user == user

    def get_absolute_url(self):
        return reverse('thread_detail', kwargs={'thread_slug': self.slug})

    def get_update_url(self):
        return reverse('thread_update', kwargs={'thread_slug': self.slug})

    def get_thread_update_form_action(self):
        return self.get_update_url()

    def get_comment_create_form_action(self, page_num):
        return '%s?page=%s#comment-form' % (
            reverse(
                'comments:comment_create',
                kwargs={'thread_slug': self.slug}
            ),
            page_num
        )

    def get_thread_follow_url(self):
        return reverse('thread_follow', kwargs={'thread_slug': self.slug})

    
    def get_follow_url(self):
        return reverse('thread_follow', kwargs={'thread_slug': self.slug})


class ThreadFollowershipQuerySet(models.query.QuerySet):
    def get_instance_and_count(self, thread, user=None):
        qs = self.filter(thread=thread)
        instance = None
        count = 0
        if user:
            qs_user = qs.select_related('user', 'first_new_comment')
            for qs_item in qs_user:
                count += 1
                if user == qs_item.user:
                    instance = qs_item
            return instance, count
        else:
            return instance, qs.count()

    def toggle(self, user, thread):
        queryset = self.filter(user=user, thread=thread)
        if queryset:
            queryset[0].delete()
        else:
            self.create(user=user, thread=thread)

    def sync_with_comment(self, thread, comment):
        qs = self.filter(thread=thread).select_related('user').all()
        user_list = [instance.user for instance in qs]
        if comment.user not in user_list:
            self.create(user=comment.user, thread=thread)
        if comment.user in user_list:
            user_list.remove(comment.user)
        self.filter(
            user__in=user_list, thread=thread,
        ).update(
            new_comment_count=F('new_comment_count') + 1
        )
        self.filter(
            user__in=user_list, thread=thread,
            first_new_comment__isnull=True
        ).update(
            first_new_comment=comment
        )


class ThreadFollowership(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    thread = models.ForeignKey('threads.Thread', on_delete=models.CASCADE)
    first_new_comment = models.ForeignKey(
        'comments.Comment', on_delete=models.CASCADE, blank=True, null=True
    )
    new_comment_count = models.PositiveIntegerField(default=0)
    objects = ThreadFollowershipQuerySet.as_manager()

    def __str__(self):
        return f'{self.thread.title} - {self.user.username}'

    def update_comment_fields(self, comments):
        if not self.first_new_comment:
            return
        next_comment = self._get_next_first_new_comment(comments)
        count = self._get_next_new_comment_count(next_comment)
        self.__class__.objects.filter(
            user=self.user, thread=self.thread,
        ).update(first_new_comment=next_comment, new_comment_count=count)

    def _get_position_of_comment_in_page(self, comments):
        position = 0
        for comment in comments:
            position += 1
            if self.first_new_comment.pk == comment.pk:
                break
        return position

    def _get_next_first_new_comment(self, comments):
        from forum.comments.models import Comment

        if comments.has_next():
            comment_qs = Comment.objects.filter(
                thread=self.thread,
                created__gt=self.first_new_comment.created
            ).exclude(is_starting_comment=True)[:COMMENT_PER_PAGE]
            if comment_qs:
                position = self._get_position_of_comment_in_page(comments)
                next_first_new_comment = comment_qs[COMMENT_PER_PAGE - position]
                return next_first_new_comment
            else:
                return None
        else:
            return None

    def _get_next_new_comment_count(self, first_new_comment):
        if first_new_comment:
            index = first_new_comment.position + first_new_comment.offset
            next_new_comment_count = self.thread.comment_count - index + 1
            return next_new_comment_count
        else:
            return 0


class ThreadRevisionQuerySet(models.query.QuerySet):
    def create_from_thread(self, thread):
        from forum.comments.models import CommentRevision
        
        # Attributes of thread.starting_comment will not be in sync with old the thread
        # so we have to fetch it from CommentRevision. This is due to the 
        # starting_comment getting updated before the thread.
        comment_revision = CommentRevision.objects.filter(
            comment=thread.starting_comment,
        ).last()
        if comment_revision:
            return self.create(
                thread=thread,
                starting_comment=comment_revision.comment,
                title=thread.title,
                message=comment_revision.message,
                marked_message=comment_revision.marked_message
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


# class ThreadActivityQuerySet(models.query.QuerySet):
#     def create_activities(self, thread, comment):
#         # # 1 - 10
#         # # read 7
#         # # 1 - 6  8 -10
#         # ThreadActivity.objects.create(
#         #     user=user,
#         #     thread=thread,
#         #     start_comment=start_comment,
#         #     end_comment=end_comment
#         # )

#         # ThreadActivity.objects.exclude(user=user).filter(
#         #     thread=thread, new_comment_count=0
#         # ).update(new_comment_count=F('new_comment_count') + 1, comment=comment)

#         # comment = ThreadActivity.objects.filter(
#         #     thread=thread, user=user).first().comment

#         # comment_pk_list[-1].created > comment.created
#         # count = 0
#         # for comment_r in comment_pk_list:
#         #     if comment_r.created >= comment.created:
#         #         count += 1
#         #     if comment_pk_list.has_next():
#         #         comment = comment_pk_list[]

#         # ThreadActivity.objects.filter(
#         #     thread=thread
#         #     user=user
#         #     new_comment_count__gte=count
#         # ).update(new_comment_count=F('new_comment_count') - count, comment=comment)

#         # Thread.objects.filter(
#         #     readers=user, threadactivity__comment_count__gt=0
#         # ).annotate(
#         #     new_c_num=F('threadactivity__new_comment_count')
#         # ).annotate(
#         #     new_c_id=F('threadactivity__new_comment')
#         # )

#         # for user in thread.followers.all():
#         #     threadactivity_qs = ThreadActivity.objects.filter(
#         #         user=user, thread=thread)
#         #     if threadactivity_qs:
#         #         threadactivity_qs.filter(
#         #             user=user, thread=thread
#         #         ).update(end_comment=comment)
#         #     else:
#         #         ThreadActivity.objects.create(
#         #             user=user, thread=thread,
#         #             start_comment=comment, end_comment=comment
#         #         )

#         #     comment_pk_list
#         #     threadactivity_qs = ThreadActivity.objects.filter(
#         #         user=user, thread=thread)
#         #     if threadactivity_qs:
#         #         for threadactivity in threadactivity_qs:
#         #             if comment[-1].created < threadactivity.end_comment.created:

#                         # if thread_activity.st
#         users = [usr for usr in thread.followers.all()
#                  if usr.pk != comment.user.pk]
#         activities = []
#         for user in users:
#             activities.append(
#                 self.model(
#                     user=user, thread=thread, comment=comment
#                 )
#             )
#         if activities:
#             self.bulk_create(activities)

#     def update_activity_actions(self, user, thread, comments):
#         queryset = self.filter(
#             user=user, thread=thread
#         ).select_related('comment')

#         comment_pk_list = []
#         for comment in comments:
#             for model in queryset:
#                 if comment.pk == model.comment.pk:
#                     comment.unread = True
#                     comment_pk_list.append(comment.pk)
#         if comment_pk_list:
#             self.filter(
#                 user=user, thread=thread, comment__in=comment_pk_list
#             ).delete()


# class ThreadActivity(TimeStampedModel):
#     comment = models.ForeignKey('comments.Comment', on_delete=models.CASCADE)
#     thread = models.ForeignKey('threads.Thread', on_delete=models.CASCADE)
#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL, on_delete=models.CASCADE
#     )
#     objects = ThreadActivityQuerySet.as_manager()

#     class Meta:
#         verbose_name_plural = 'Thread Activities'
