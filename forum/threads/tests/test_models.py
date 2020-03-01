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

    def test_synchronise_for_create(self):
        self.assertEquals(self.thread.comment_count, 0)
        comment = make_comment(self.user, self.thread)
        self.thread.synchronise(comment)
        self.thread.refresh_from_db()
        self.assertEquals(self.thread.comment_count, 1)

        comment2 = make_comment(self.user, self.thread)
        self.thread.synchronise(comment2)
        self.thread.refresh_from_db()
        self.assertEquals(self.thread.comment_count, 2)

        comment3 = make_comment(self.user, self.thread)
        self.thread.synchronise(comment3, added=False)
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

        # revision = ThreadRevision.objects.create_from_thread(self.thread)
        # self.assertIsNotNone(revision)
        # self.assertEquals(self.thread, revision.thread)
