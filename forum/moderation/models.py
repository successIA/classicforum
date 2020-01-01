from django.db import models
from django.conf import settings
from django.utils import timezone

from forum.categories.models import Category
from forum.core.models import TimeStampedModel


class ModeratorQuerySet(models.query.QuerySet):	
	def get_for_category(self, cat):
		return self.filter(categories=cat)


class Moderator(TimeStampedModel):
	user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True
    )
	categories = models.ManyToManyField("categories.Category")
	objects = ModeratorQuerySet.as_manager()

	def __str__(self):
		return self.user.username


class ModeratorEvent(models.Model):
	MODERATOR_ADDED = 0
	MODERATOR_REMOVED = 1
	CATEGORY_ADDED = 2
	CATEGORY_REMOVED = 3

	EVENT_TYPE_CHOICES = (
		(MODERATOR_ADDED, 'added_moderator'),
		(MODERATOR_REMOVED, 'removed_moderator'),
		(CATEGORY_ADDED, 'added_category'),
		(CATEGORY_REMOVED, 'removed_category')
	)
	event_type = models.PositiveSmallIntegerField(choices=EVENT_TYPE_CHOICES)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	categories = models.ManyToManyField("categories.Category")
	created_at = models.DateTimeField(default=timezone.now)

	def __str__(self):
		event_type = self.__class__.EVENT_TYPE_CHOICES[self.event_type][1]
		return f"{self.user.username} - {event_type}"

