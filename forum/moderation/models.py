from django.db import models
from django.conf import settings
from django.utils import timezone

from forum.core.models import TimeStampedModel


class Moderator(TimeStampedModel):
	user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True
    )
	categories_moderating = models.ManyToManyField("categories.Category")

	def save(self, *args, **kwargs):
		created = True if self.pk else False
		super(Moderator, self).save(*args, **kwargs)		

	def delete(self, *args, **kwargs):
		categories = self.categories.all()
		super(Moderator, self).delete(*args, **kwargs)
		ModeratorEvent.objects.create_event(
			ModeratorEvent.MODERATOR_REMOVED, user=self.user
		)
    
class ModeratorEventQuerySet(models.query.QuerySet):
	def create_event(self, event_type, user, categories):
		event = self.create(event_type=event_type, user=user)
		event.categories.add(*categories) 

	
class ModeratorEvent(models.Model):
	MODERATOR_ADDED = 0
	MODERATOR_REMOVED = 1
	CATEGORY_ADDED = 3
	CATEGORY_REMOVED = 4

	EVENT_TYPE_CHOICES = (
		(MODERATOR_ADDED, 'added_moderator'),
		(MODERATOR_REMOVED, 'removed_moderator'),
		(CATEGORY_ADDED, 'added_category'),
		(CATEGORY_REMOVED, 'removed_category')
	)
	event_type = models.PositiveSmallIntegerField(choices=EVENT_TYPE_CHOICES)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	categories = models.ManyToManyField("categories.Category")
	created_at = models.DateTimeField(default=timezone.now())
		

