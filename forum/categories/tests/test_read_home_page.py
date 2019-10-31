from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from django.test import TestCase

from forum.categories.models import Category

class CategoryListTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.category = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='django')

    def test_a_visitor_see_the_the_home_page(self):
        # when a user visits the site, he see the title Forum
        response = self.client.get('/')
        self.assertIn(b"Forum", response.content)

    def test_a_visitor_can_see_all_the_categories(self):
        response = self.client.get('/')
        self.assertIn(self.category.title, response.content.decode())

    def test_a_visitor_can_see_a_single_category(self):
        response = self.client.get(self.category.get_absolute_url())
        self.assertIn(self.category.title, response.content.decode())
