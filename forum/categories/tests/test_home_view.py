from django.core.urlresolvers import reverse, resolve
from django.test.client import RequestFactory
from django.test import TestCase

from forum.categories.views import CategoryListView

from forum.categories.models import Category, create_category_slug

from forum import testutils


class HomeTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='django')
        url = reverse('home')
        self.response = self.client.get(url)

    def test_home_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_home_url_resolves_home_view(self):
        """ check if resolve and home routes to the same url"""
        view = resolve('/')
        self.assertEquals(view.func.view_class, CategoryListView)

    def test_home_page_contains_link_to_category_detail_page(self):
        category_url = reverse('category_detail', kwargs={'slug': self.category.slug})
        self.assertContains(self.response, 'href="{0}"'.format(category_url))

    def test_home_page_contains_threads_context(self):
        thread = testutils.create_thread(self)
        url = reverse('home')
        response = self.client.get(url)
        self.assertEquals(response.context.get('threads', None).first(), thread)
