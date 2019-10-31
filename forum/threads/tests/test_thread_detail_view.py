from django.core.urlresolvers import reverse, resolve
from django.test.client import RequestFactory
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile


from forum.categories.models import Category
from forum.threads.models import Thread
from forum.comments.views import CommentListView
from forum.comments.models import Comment
from forum.image_app.models import Image
from forum.accounts.models import UserProfile
from forum import testutils


import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath('__file__')))
image_path = os.path.join(BASE_DIR, 'forum_project', 'forum', 'threads', 'tests', 'images', 'marketing1.jpg')


class ThreadDetailTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='john', email='john@example.com', password='pass1234')
        UserProfile.objects.create(user=self.user)
        self.category = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='django')
        self.thread = Thread.objects.create(title='Galaxy S5 Discussion Thread', body='Lorem ipsum dalor', category=self.category, user=self.user)
        self.response = self.client.get(self.thread.get_absolute_url())

    def test_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_a_thread_detail_view_function(self):
        view = resolve(self.thread.get_absolute_url())
        self.assertEquals(view.func.view_class, CommentListView)

    def test_a_thread_should_belong_to_a_category(self):
        self.assertEquals(self.category.thread_set.first(), self.thread)

    def test_a_thread_should_belong_to_a_user(self):
        self.assertEquals(self.user.thread_set.first(), self.thread)

    def test_thread_detail_page_has_a_thread_context(self):
        self.assertEqual(self.response.context.get('thread', None), self.thread)

    def test_thread_detail_page_has_a_category_context(self):
        self.assertEqual(self.response.context.get('category', None), self.category)

    def test_a_thread_detail_page_contains_a_title(self):
        self.assertContains(self.response, self.thread.title)

    def test_a_thread_detail_page_contains_a_body(self):
        self.assertContains(self.response, self.thread.body)

    def test_a_thread_detail_page_has_a_category_with_title(self):
        response = self.client.get(self.thread.get_absolute_url())
        self.assertContains(response, self.category.title)

    def test_a_thread_detail_view_may_not_have_a_comment(self):
        self.assertEquals(self.thread.comments.first(), None)

    def test_a_thread_may_have_a_comment(self):
        comment = Comment.objects.create(message='Hello World!', thread=self.thread, user=self.user)
        self.assertEquals(self.thread.comments.first(), comment)

    def test_a_thread_detail_page_may_not_have_comment(self):
        self.assertContains(self.response, 'Be the first to comment')

    def test_a_thread_detail_page_contains_a_comment_with_message(self):
        comment = Comment.objects.create(message='Hello World!', thread=self.thread, user=self.user)
        response = self.client.get(self.thread.get_absolute_url())
        self.assertContains(response, comment.message)

    def test_a_thread_detail_page_contains_a_comment_with_username(self):
        comment = Comment.objects.create(message='Hello World!', thread=self.thread, user=self.user)
        response = self.client.get(self.thread.get_absolute_url())
        self.assertContains(response, comment.user.username)

    def test_thread_contains_a_button_to_comment_form(self):
        self.assertIn('Reply', self.response.content.decode())

    def test_thread_contains_link_to_comment_page(self):
        self.assertIn(self.thread.get_comment_create_url(), self.response.content.decode())

    def test_a_thread_page_contains_link_to_like_comment(self):
        self.assertIn(self.thread.get_comment_create_url(), self.response.content.decode())

