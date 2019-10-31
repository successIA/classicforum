from django.core.urlresolvers import reverse, resolve
from django.test.client import RequestFactory
from django.test import TestCase
from django.contrib.auth.models import User

from forum.categories.models import Category
from forum.threads.models import Thread
from forum.categories.views import CategoryDetailView
from forum.accounts.models import UserProfile


class CategoryDetailTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='john', email='john@example.com', password='pass1234')
        self.userprofile = UserProfile.objects.create(user=self.user) 
        self.category = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='django')
        self.response = self.client.get(self.category.get_absolute_url())

    def test_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_a_category_detail_view_function(self):
        view = resolve('/categories/django/')
        self.assertEquals(view.func.view_class, CategoryDetailView)

    def test_category_detail_page_has_a_category_context(self):
        self.assertEqual(self.response.context.get('category', None), self.category)

    def test_a_category_detail_page_contains_a_title(self):
        self.assertContains(self.response, self.category.title)

    def test_a_category_detail_view_may_have_a_thread(self):
        thread = Thread.objects.create(title='Galaxy S5 Discussion Thread', body='Lorem ipsum dalor', category=self.category, user=self.user)
        self.assertEquals(self.category.thread_set.first(), thread)

    def test_a_category_detail_page_has_a_thread_with_title(self):
        thread = Thread.objects.create(title='Galaxy S5 Discussion Thread', body='Lorem ipsum dalor', category=self.category, user=self.user)
        response = self.client.get(self.category.get_absolute_url())
        self.assertContains(response, thread.title)

    def test_a_category_detail_view_may_not_have_a_thread(self):
        self.assertEquals(self.category.thread_set.first(), None)

    def test_a_category_detail_page_may_not_have_thread(self):
        self.assertContains(self.response, 'This category does not have a thread')

    def test_a_category_detail_page_links_to_a_thread(self):
        thread = Thread.objects.create(title='Django1', body='Lorem ipsum dalor', category=self.category, user=self.user)
        response = self.client.get(self.category.get_absolute_url())
        self.assertContains(response, 'href="{0}"'.format(thread.get_absolute_url()))

    # def test_a_visitor_can_see_a_single_category(self):
    #     response = self.client.get(self.category.get_absolute_url())
    #     self.assertIn(self.category.title, response.content.decode())
