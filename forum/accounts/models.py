from datetime import timedelta

from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse_lazy, reverse
from django.contrib.contenttypes.fields import GenericRelation
from django.db.models import Max, Min, Count, F, Value, CharField, Prefetch
from django.utils import timezone

from forum.core.models import TimeStampedModel


class UserProfile(models.query.QuerySet):

    def get_related(self):
        return self.select_related(
            'user'
        ).prefetch_related(
            'followers__userprofile__user',
            'following__userprofile__user',
            # 'attachment_set'
        )


class UserProfile(TimeStampedModel):
    GENDER_OPTIONS = (
        ('M', 'Male'),
        ('F', 'Female')
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    gender = models.CharField(
        max_length=20, choices=GENDER_OPTIONS, blank=True)
    signature = models.TextField(max_length=127, blank=True)
    location = models.CharField(max_length=32, blank=True)
    website = models.URLField(max_length=50, blank=True)
    followers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='followers', blank=True
    )
    following = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='following', blank=True
    )
    last_seen = models.DateTimeField(default=timezone.now)
    email_confirmed = models.BooleanField(default=False)
    avatar_url = models.CharField(max_length=255, blank=True, null=True)
    objects = UserProfile.as_manager()

    def __str__(self):
        return self.user.username

    def is_online(self):
        timeout = 5 * 60  # 5 minutes.
        return timezone.now() < self.last_seen + timedelta(seconds=timeout)

    def is_owner(self, user):
        return self.user == user

    def is_required_filter_owner(self, user, filter_str):
        owner_only = ['following', 'new']
        if filter_str not in owner_only:
            return True
        return self.is_owner(user)

    def has_avatar(self):
        return self.attachment_set.count() > 0

    def get_avatar_url(self):
        return self.attachment_set.first().image.url

    def toggle_followers(self, follower):
        if follower not in self.followers.all():
            self.followers.add(follower)
        else:
            self.followers.remove(follower)

    def toggle_following(self, user):
        if user not in self.following.all():
            self.following.add(user)
        else:
            self.following.remove(user)

    def get_absolute_url(self):
        return reverse('accounts:user_stats', kwargs={'username': self.user.username})

    def get_user_follow_url(self):
        return reverse('accounts:user_follow', kwargs={'username': self.user.username})

    def get_userprofile_update_url(self):
        return reverse('accounts:user_profile_update', kwargs={'username': self.user.username})

    def get_login_url(self):
        return reverse('accounts:login')
