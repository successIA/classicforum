from django.urls import reverse
from django.utils import timezone

from faker import Faker
from test_plus import TestCase

from forum.categories.models import Category
from forum.comments.models import Comment
from forum.threads.models import Thread

from forum.comments.tests.utils import make_comment

fake = Faker()


class CommentModelTest(TestCase):
    def setUp(self):
        self.user = self.make_user("testuser1")
        self.category = Category.objects.create(
            title="progromming group", description="NA"
        )
        self.thread = Thread.objects.create(
            title="python discussion",
            body="NA",
            user=self.user,
            category=self.category
        )
        self.comment = Comment.objects.create(
            message='test message',
            user=self.user,
            thread=self.thread,
            is_starting_comment=True
        )

    # def test_delete(self):
    #     second_user = self.make_user('testuser2')
    #     comment1 = Comment.objects.create(
    #         message='test message1', user=self.user, thread=self.thread
    #     )
    #     comment2 = Comment.objects.create(
    #         message='test message2', user=self.user, thread=self.thread
    #     )
    #     self.assertEquals(Comment.objects.count(), 3)
    #     comment1.delete()
    #     self.assertEquals(Comment.objects.count(), 2)
    #     comment2.refresh_from_db()
    #     self.assertEquals(comment2.offset, -1)
    #     self.comment.delete()
    #     self.assertEquals(Comment.objects.count(), 1)
    #     comment2.refresh_from_db()
    #     self.assertEquals(comment2.offset, -2)

    def test_is_owner(self):
        second_user = self.make_user('testuser2')
        self.assertFalse(self.comment.is_owner(second_user))
        self.assertTrue(self.comment.is_owner(self.user))

    def test_toggle_like_with_new_liker(self):        
        second_user = self.make_user('testuser2')
        self.comment.toggle_like(second_user)
        self.assertIn(second_user, self.comment.likers.all())

    def test_toggle_like_with_liker(self):
        second_user = self.make_user('testuser2')
        self.comment.likers.add(second_user)
        self.comment.toggle_like(second_user)
        self.assertNotIn(second_user, self.comment.likers.all())

    