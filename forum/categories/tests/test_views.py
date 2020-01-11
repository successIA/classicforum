from forum.threads.models import Thread
from test_plus import TestCase
from django.urls import reverse
from django.core.paginator import Page

from forum.threads.forms import ThreadForm
from forum.categories.models import Category
from forum.threads.tests.utils import make_only_thread


class CategoryViewTest(TestCase):
    def setUp(self):
        self.user = self.make_user('john')
        self.category = Category.objects.create(
            title='progromming group', description='NA'
        )


class CategoryDetailView(CategoryViewTest):
    def setUp(self):
        super().setUp()
        make_only_thread(self.user, self.category, count=15)
        self.detail_url = reverse(
            'categories:category_detail',
            kwargs={'slug': self.category.slug}
        )

    def test_wrong_slug(self):
        response = self.client.get(self.detail_url)
        Category.objects.all().delete()
        response = self.client.get('/categories/random-slug/')
        self.assertEquals(response.status_code, 404)

    def test_no_thread(self):
        Thread.objects.all().delete()
        response = self.client.get(self.detail_url)
        self.assertEquals(response.status_code, 200)
        # no_threads_str = 'No Available threads for the current selection.'
        no_threads_str = 'No threads yet'
        self.assertIn(no_threads_str, response.content.decode())
        self.assertEquals(response.context['category'], self.category)
        self.assertIsInstance(response.context['form'], ThreadForm)
        self.assertEquals(
            response.context['form'].initial['category'], self.category
        )
        self.assertEquals(response.context['dropdown_active_text'], 'recent')
        self.assertIsInstance(response.context['threads'], Page)
        self.assertEquals(response.context['threads'].number, 1)
        self.assertEquals(
            response.context['base_url'],  
            [f'/categories/progromming-group/recent/', '/']
        )
        form_action = '%s#comment-form' % reverse(
            'categories:category_thread_create',
            kwargs={'slug': self.category.slug,
                    'filter_str': 'recent', 'page': 1}
        )
        self.assertEquals(response.context['form_action'], form_action)

    def test_one_thread(self):
        Thread.objects.all().delete()
        thread = make_only_thread(self.user, self.category)
        response = self.client.get(self.detail_url)
        no_threads_str = 'No Available threads for the current selection.'
        self.assertNotIn(no_threads_str, response.content.decode())
        self.assertEquals(response.context['threads'][0], thread)

    def test_many_threads(self):
        # make_only_thread(self.user, self.category, count=15)
        response = self.client.get(self.detail_url)
        self.assertEquals(len(response.context['threads']), 10)
        filter_str_url = reverse(
            "categories:category_detail_filter",
            kwargs={'slug': self.category.slug,
                    'filter_str': 'recent', 'page': 2}
        )
        response = self.client.get(filter_str_url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(response.context['threads']), 5)

    def test_all_threads_filter_str(self):
        for filter_str in ['recent', 'trending', 'popular', 'fresh']:
            filter_str_url = reverse(
                "categories:category_detail_filter",
                kwargs={'slug': self.category.slug,
                        'filter_str': filter_str, 'page': 1}
            )
            response = self.client.get(filter_str_url)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(
                response.context['dropdown_active_text'], filter_str
            )
            self.assertEquals(
                response.context['base_url'],
                [f'/categories/{self.category.slug}/{filter_str}/', '/']
            )

    def test_auth_filter_str_for_anonymous_user(self):
        auth_filter_str_list = ['new', 'following']
        # auth_filter_str_list = ['new', 'following', 'me']
        for filter_str in auth_filter_str_list:
            filter_str_url = reverse(
                "categories:category_detail_filter",
                kwargs={'slug': self.category.slug,
                        'filter_str': filter_str, 'page': 1}
            )
            response = self.client.get(filter_str_url)
            self.assertEquals(response.status_code, 404)

    def test_auth_filter_str_for_authenticated_user(self):
        auth_filter_str_list = ['new', 'following', 'me']
        self.make_user('user1')
        self.client.login(username='user1', password='password')
        for filter_str in auth_filter_str_list:
            filter_str_url = reverse(
                "categories:category_detail_filter",
                kwargs={'slug': self.category.slug,
                        'filter_str': filter_str, 'page': 1}
            )
            response = self.client.get(filter_str_url)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(
                response.context['dropdown_active_text'], filter_str
            )
            self.assertEquals(
                response.context['base_url'],
                [f'/categories/{self.category.slug}/{filter_str}/', '/']
            )
