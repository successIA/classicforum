from django.db import models
from django.conf import settings
from django.shortcuts import reverse
from django.utils import timezone

from forum.categories.models import Category
from forum.comments.models import Comment
from forum.core.models import TimeStampedModel
from forum.threads.models import Thread


class ModeratorQuerySet(models.query.QuerySet):	
	def get_for_category(self, cat):
		return self.filter(categories=cat)


class Moderator(TimeStampedModel):
	user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True
    )
	categories = models.ManyToManyField("categories.Category")
	hidden_threads = models.ManyToManyField("threads.Thread")
	hidden_comments = models.ManyToManyField("comments.Comment")
	objects = ModeratorQuerySet.as_manager()

	def __str__(self):
		return self.user.username
	
	def _get_hidden_posts(self, post):
		if isinstance(post, Thread):
			return self.hidden_threads.all()
		if isinstance(post, Comment):
			return self.hidden_comments.all()
		raise TypeError(
			"post has to be an instance either Thread or Comment"
		)

	def is_owner(self, request_mod):
		return self == request_mod
	
	def is_supermoderator_to(self, obj):
		obj_pk_list = [c.pk for c in obj.categories.all()]
		return (
			self.user.is_supermoderator and 
			self.categories.filter(pk__in=obj_pk_list).exists()
		)

	def is_moderating_post(self, post):
		return post.category in self.categories.all()

	def is_supermoderator_and_moderating_post(self, post):
		return self.user.is_supermoderator and self.is_moderating_post(post)

	def can_hide_post(self, post):
		is_starting_comment = (
			isinstance(post, Comment) and post.is_starting_comment
		)
		if (
			post.visible and self.is_moderating_post(post) 
			and not is_starting_comment
		):
			if not post.user.is_moderator:
				return True
			if post.user.moderator.is_owner(self):
				return True
			if not post.user.moderator.is_moderating_post(post):
				return True
			if self.is_supermoderator_and_moderating_post(post):
				return True
		return False
	
	def can_unhide_post(self, post):
		if not post.visible and self.is_moderating_post(post):
			if post in self._get_hidden_posts(post) or (
				self.is_supermoderator_and_moderating_post(post)
			):
				return True
		return False

	def get_common_categories(self, obj):
		if obj.user == self.user:
			return self.categories.all()
		else:
			obj_pk_list = [c.pk for c in obj.categories.all()]
			return self.categories.filter(pk__in=obj_pk_list).all()

	def get_absolute_url(self):
		return reverse(
			"moderation:moderator_detail", 
			kwargs={"username": self.user.username}
		)
	
	@staticmethod
	def get_post_hide_action_url(comment):
		if comment.is_starting_comment:
			return reverse(
				"moderation:thread_hide", 
				kwargs={"slug": comment.thread.slug}
			)
		else:
			return reverse(
				"moderation:comment_hide", 
				kwargs={
					"thread_slug": comment.thread.slug, 
					"comment_pk": comment.pk
				}
			)


	# @staticmethod
	# def _get_thread_hide_action_url(thread):
	# 	return reverse(
	# 		"moderation:thread_hide", kwargs={"slug": thread.slug}
	# 	)
		
	# @staticmethod
	# def _get_comment_hide_action_url(comment):
	# 	return reverse(
	# 		"moderation:comment_hide", 
	# 		kwargs={"thread_slug": comment.thread.slug, "comment_pk": comment.pk}
	# 	)


class ModeratorEvent(models.Model):
	MODERATOR_ADDED = 0
	MODERATOR_REMOVED = 1
	CATEGORY_ADDED = 2
	CATEGORY_REMOVED = 3
	THREAD_HIDDEN = 4
	THREAD_UNHIDDEN = 5
	COMMENT_HIDDEN = 6
	COMMENT_UNHIDDEN = 7

	EVENT_TYPE_CHOICES = (
		(MODERATOR_ADDED, "added_moderator"),
		(MODERATOR_REMOVED, "removed_moderator"),
		(CATEGORY_ADDED, "added_category"),
		(CATEGORY_REMOVED, "removed_category"),
		(THREAD_HIDDEN, "Make thread invisible"),
		(THREAD_UNHIDDEN, "Make thread visible"),
		(COMMENT_HIDDEN, "Make comment invisible"),
		(COMMENT_UNHIDDEN, "Make comment visible"),
	)
	event_type = models.PositiveSmallIntegerField(choices=EVENT_TYPE_CHOICES)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	categories = models.ManyToManyField("categories.Category")
	thread = models.ForeignKey(
		"threads.Thread", null=True, blank=True, on_delete=models.CASCADE
	)
	comment = models.ForeignKey(
		"comments.Comment", null=True, blank=True, on_delete=models.CASCADE
	)
	created_at = models.DateTimeField(default=timezone.now)

	def __str__(self):
		event_type = self.__class__.EVENT_TYPE_CHOICES[self.event_type][1]
		return f"{self.user.username} - {event_type}"

