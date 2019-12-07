from django.urls import reverse
from django.utils import timezone

from faker import Faker
from test_plus import TestCase

from forum.categories.models import Category, CategoryQuerySet
from forum.threads.models import (
    Thread, ThreadFollowership, ThreadRevision
)
from forum.comments.tests.utils import make_comment

fake = Faker()


class ThreadModelTest(TestCase):
    def setUp(self):
        self.user = self.make_user("john")
        self.category = Category.objects.create(
            title="progromming group",
            description="NA"
        )
        self.thread = Thread.objects.create(
            title="python discussion",
            body="NA",
            user=self.user,
            category=self.category,
            created=timezone.now(),
            modified=timezone.now()
        )

    def test_save(self):
        self.assertEquals(self.thread.slug, "python-discussion")
        self.assertIn(self.user, self.thread.followers.all())

    def test_sync_with_comment_for_create(self):
        self.assertEquals(self.thread.comment_count, 0)
        comment = make_comment(self.user, self.thread)
        self.thread.sync_with_comment(comment)
        self.thread.refresh_from_db()
        self.assertEquals(self.thread.comment_count, 1)

        comment2 = make_comment(self.user, self.thread)
        self.thread.sync_with_comment(comment2)
        self.thread.refresh_from_db()
        self.assertEquals(self.thread.comment_count, 2)

        comment3 = make_comment(self.user, self.thread)
        self.thread.sync_with_comment(comment3, is_create=False)
        self.thread.refresh_from_db()
        self.assertEquals(self.thread.comment_count, 1)
        self.assertEquals(self.thread.final_comment_user, comment3.user)
        self.assertEquals(self.thread.final_comment_time, comment3.created)

    def test_toggle_follower(self):
        second_user = self.make_user('second_user')
        ThreadFollowership.objects.toggle(second_user, self.thread)

        self.assertIn(second_user, self.thread.followers.all())
        ThreadFollowership.objects.toggle(second_user, self.thread)

        self.assertNotIn(second_user, self.thread.followers.all())

    def test_is_owner(self):
        self.assertTrue(self.thread.is_owner(self.user))


class ThreadRevisionQuerySetTest(ThreadModelTest):
    def setUp(self):
        super().setUp()

    def test_create_from_thread(self):
        comment = make_comment(
            self.user, self.thread, is_starting_comment=True
        )
        self.thread.starting_comment = comment
        self.thread.save()
        comment.message = 'Updated message'
        comment.save()
        self.thread.title = 'Updated title'
        self.thread.save()

        revision = ThreadRevision.objects.create_from_thread(self.thread)
        self.assertIsNotNone(revision)
        self.assertEquals(self.thread, revision.thread)


# class ThreadActivityQuerySetTest(ThreadModelTest):
#     def setUp(self):
#         super().setUp()

#     def test_create_activities(self):
#         comment = make_comment(self.user, self.thread)
#         ThreadActivity.objects.create_activities(self.thread, comment)
#         activity = ThreadActivity.objects.filter(
#             comment=comment, thread=self.thread
#         ).first()
#         self.assertIsNone(activity)

#         second_user = self.make_user('second_user')
#         comment2 = make_comment(self.user, self.thread)
#         self.thread.followers.add(second_user)
#         self.thread.refresh_from_db()
#         ThreadActivity.objects.create_activities(self.thread, comment2)
#         activity2 = ThreadActivity.objects.filter(
#             comment=comment2, thread=self.thread
#         ).first()
#         self.assertEquals(activity2.user, second_user)

#     def test_update_activity_actions(self):
#         second_user = self.make_user('second_user')
#         comment2 = make_comment(self.user, self.thread)
#         self.thread.followers.add(second_user)
#         self.thread.refresh_from_db()
#         ThreadActivity.objects.create_activities(self.thread, comment2)
#         comments = []
#         comments.append(comment2)
#         ThreadActivity.objects.update_activity_actions(
#             second_user, self.thread, comments
#         )
#         activity2 = ThreadActivity.objects.filter(
#             user=second_user, thread=self.thread, comment=comment2
#         ).first()
#         self.assertIsNone(activity2)
