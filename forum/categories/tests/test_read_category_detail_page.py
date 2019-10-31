from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from django.test import TestCase
from django.contrib.auth.models import User

from forum.categories.models import Category
from forum.threads.models import Thread
from forum.accounts.models import UserProfile


class CategoryDetailTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='john', email='john@example.com', password='pass1234')
        self.userprofile = UserProfile.objects.create(user=self.user)
        self.category = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='django')
        self.thread1 = Thread.objects.create(title='Django1', body='The Web Framework For The Perfectionist', category=self.category, user=self.user)
        self.thread2 = Thread.objects.create(title='Django2', body='The Web Framework For The Perfectionist', category=self.category, user=self.user)
        self.thread3 = Thread.objects.create(title='Django3', body='The Web Framework For The Perfectionist', category=self.category, user=self.user)
        self.response = self.client.get(self.category.get_absolute_url())

    def test_a_visitor_can_see_the_title_of_category(self):
        # when a visitor visits a category , he can see the title of the category
        self.assertContains(self.response, self.category.title)

    #  def test_a_visitor_can_may_see_the_title_of_thread_in_category

    #  def test_a_visitor_can_visit_a_thread_on_page

    #  def test_a_visitor_can_go_back_to_the_home_page

    # def test_a_visitor_can_see_all_the_threads_that_belong_to_a_category(self):
    #     self.assertContains(self.response, self.thread1.title)
    #     self.assertContains(self.response, self.thread2.title)
    #     self.assertContains(self.response, self.thread3.title)

    # def test_a_visitor_can_see_a_single_category(self):
    #     response = self.client.get(self.category.get_absolute_url())
    #     self.assertIn(self.category.title, response.content.decode())
