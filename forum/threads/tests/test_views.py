from django.core.paginator import Page
from django.urls import reverse
from django.utils import timezone

from faker import Faker
from test_plus import TestCase

from forum.accounts.tests.utils import login
from forum.categories.models import Category, CategoryQuerySet
from forum.categories.tests.utils import make_category
from forum.comments.forms import CommentForm
from forum.moderation.tests.utils import make_moderator
from forum.threads.forms import ThreadForm
from forum.threads.models import (
    Thread, ThreadRevision
)
from forum.comments.tests.utils import make_comment
from forum.threads.tests.utils import make_threads, make_only_thread

fake = Faker()


class ThreadsViewsTest(TestCase):
    def setUp(self):
        self.user = self.make_user('testuser1')
        self.category = make_category()


class ThreadListViewTest(ThreadsViewsTest):
    def setUp(self):
        super().setUp()
        make_only_thread(self.user, self.category, count=15)
        self.list_url = reverse('home')

    def test_no_thread(self):
        Thread.objects.all().delete()
        response = self.client.get(self.list_url)
        self.assertEquals(response.status_code, 200)
        no_threads_str = "No Available threads at this moment. Start a new thread or check back later."
        self.assertIn(no_threads_str, response.content.decode())
        self.assertEquals(response.context['form'], ThreadForm)
        # self.assertEquals(
        #     response.context['form'].initial['category'], self.category
        # )
        self.assertEquals(response.context['current_thread_filter'], 'recent')
        self.assertIsInstance(response.context['threads'], Page)
        self.assertEquals(response.context['threads'].number, 1)
        self.assertEquals(
            response.context['base_url'], [f"/threads/recent/", "/"]
        )
        form_action = '%s#post-form' % reverse(
            'threads:thread_create',
            kwargs={'filter_str': 'recent', 'page': 1}
        )
        self.assertEquals(response.context['form_action'], form_action)

    def test_many_threads(self):
        response = self.client.get(self.list_url)
        self.assertEquals(len(response.context['threads']), 10)

        url = reverse(
            "threads:thread_list_filter",
            kwargs={'filter_str': 'recent', 'page': 2}
        )
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(response.context['threads']), 5)

    def test_all_threads_filter_str(self):
        for filter_str in ['recent', 'trending', 'popular', 'fresh']:
            url = reverse(
                "threads:thread_list_filter",
                kwargs={'filter_str': filter_str, 'page': 1}
            )
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(
                response.context['current_thread_filter'], filter_str
            )
            self.assertEquals(
                response.context['base_url'], [f"/threads/{filter_str}/", "/"]
            )

    def test_auth_threads_filter_with_anonymous_user(self):
        # auth_filter_str_list = ['new', 'following', 'me']
        auth_filter_str_list = ['new', 'following']
        for filter_str in auth_filter_str_list:
            url = reverse(
                "threads:thread_list_filter",
                kwargs={'filter_str': filter_str, 'page': 1}
            )
            response = self.client.get(url)
            self.assertEquals(response.status_code, 404)

    def test_auth_threads_filter_with_authenticated_user(self):
        self.make_user('user1')
        self.client.login(username='user1', password='password')
        auth_filter_str_list = ['new', 'following', 'me']
        for filter_str in auth_filter_str_list:
            url = reverse(
                "threads:thread_list_filter",
                kwargs={'filter_str': filter_str, 'page': 1}
            )
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(
                response.context['current_thread_filter'], filter_str
            )
            self.assertEquals(
                response.context['base_url'], [f"/threads/{filter_str}/", "/"]
            )
    
    # def test_view_should_not_render_hidden_thread_for_regular_user(self):
    #     Thread.objects.all().delete()
    #     thread = make_threads(visible=False)
    #     response = self.client.get(self.list_url)
    #     self.assertEquals(len(response.context['threads']), 0)

    #     thread = make_threads()
    #     response = self.client.get(self.list_url)
    #     self.assertEquals(len(response.context['threads']), 1)
    #     self.assertEquals(Thread.objects.count(), 2)

    # def test_view_should_render_hidden_thread_for_moderator(self):
    #     Thread.objects.all().delete()
    #     thread = make_threads(visible=False)
    #     login(self, self.user, 'password')
    #     make_moderator(self.user, thread.category)
    #     response = self.client.get(f"{self.list_url}")
    #     self.assertEquals(len(response.context['threads']), 1)

    #     thread = make_threads()
    #     response = self.client.get(f"{self.list_url}")
    #     self.assertEquals(len(response.context['threads']), 2)
    #     self.assertEquals(Thread.objects.count(), 2)


class ThreadCreateViewTest(ThreadsViewsTest):
    def setUp(self):
        super().setUp()
        self.create_url = reverse(
            'threads:thread_create',
            kwargs={'filter_str': 'recent', 'page': 1},
        )
        self.create_url2 = reverse(
            'categories:category_thread_create',
            kwargs={'slug': self.category.slug,
                    'filter_str': 'recent', 'page': 1},
        )

    def test_anonymous_user_redirect(self):
        redirect_url = '%s?next=%s' % (
            reverse('accounts:login'), self.create_url
        )
        redirect_url2 = '%s?next=%s' % (
            reverse('accounts:login'), self.create_url2
        )

        get_response = self.client.get(self.create_url)
        self.assertRedirects(get_response, redirect_url)
        get_response2 = self.client.get(self.create_url2)
        self.assertRedirects(get_response2, redirect_url2)

        data = {
            'category': self.category.pk,
            'title': 'python programming',
            'message': 'hello word'
        }
        post_response = self.client.post(self.create_url, data)
        self.assertRedirects(post_response, redirect_url)
        post_response2 = self.client.post(self.create_url2, data)
        self.assertRedirects(post_response2, redirect_url2)

    def test_view_render_for_authenticated_user(self):
        login(self, self.user, 'password')

        response = self.client.get(self.create_url)
        self.assertEquals(response.status_code, 200)

        response2 = self.client.get(self.create_url2)
        self.assertEquals(response2.status_code, 200)

        self.assertEquals(response.context['form'], ThreadForm)
        self.assertIsInstance(response2.context['form'], ThreadForm)

    def test_view_submit_success_for_authenticated_user(self):
        login(self, self.user, 'password')
        data = {
            'category': self.category.pk,
            'title': 'python programming',
            'message': 'hello word'
        }

        response = self.client.post(self.create_url, data)
        self.assertEquals(response.status_code, 302)

        response2 = self.client.post(self.create_url2, data)
        self.assertEquals(response2.status_code, 302)

        self.assertTrue(Thread.objects.exists())

    def test_empty_data_rejection(self):
        login(self, self.user, 'password')
        data = {}

        response = self.client.post(self.create_url, data)
        self.assertEquals(response.status_code, 200)
        form = response.context.get('form')
        self.assertTrue(form.errors)

        response2 = self.client.post(self.create_url2, data)
        self.assertEquals(response2.status_code, 200)
        form2 = response.context.get('form')
        self.assertTrue(form.errors)

    def test_invalid_data_rejection(self):
        login(self, self.user, 'password')
        data = {
            'category': 'Choose category',
            'title': '',
            'message': '',
        }

        response = self.client.post(self.create_url, data)
        self.assertEquals(response.status_code, 200)
        form = response.context.get('form')
        self.assertTrue(form.errors)

        response2 = self.client.post(self.create_url2, data)
        self.assertEquals(response2.status_code, 200)
        form2 = response.context.get('form')
        self.assertTrue(form2.errors)


class ThreadDetailViewTest(ThreadsViewsTest):
    def setUp(self):
        super().setUp()
        # Returns a thread without starting comment
        self.thread = make_only_thread(self.user, self.category)
        self.detail_url = reverse(
            'thread_detail', kwargs={'thread_slug': self.thread.slug}
        )

    def test_random_slug(self):
        url = reverse('thread_detail', kwargs={'thread_slug': 'random-slug'})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

    def test_no_starting_comment(self):
        response = self.client.get(self.detail_url)
        self.assertEquals(response.status_code, 200)
        report = "Something went wrong. Please try updating the thread if you were the author."
        self.assertIn(report, response.content.decode())
        self.assertEquals(response.context['thread'], self.thread)

    def test_starting_comment_and_no_reply(self):
        # Delete all the threads to make way for a thread with starting
        # comment.
        Thread.objects.all().delete()
        thread = make_threads(1, self.user, self.category)
        url = reverse('thread_detail', kwargs={'thread_slug': thread.slug})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

        report = "Be the first to comment"
        self.assertIn(report, response.content.decode())

        self.assertEquals(response.context['thread'], thread)
        self.assertIn('thread_followers_count', response.context)
        self.assertEquals(
            response.context['starting_comment'], thread.starting_comment
        )
        self.assertEquals(response.context['form'], CommentForm)
        self.assertIn('category', response.context)
        self.assertIn('comments', response.context)
        self.assertIn('form_action', response.context)
        self.assertIn('first_page', response.context)
        self.assertNotIn('is_thread_follower', response.context)

    def test_context_for_authenticated_user(self):
        login(self, self.user.username, 'password')
        response = self.client.get(self.detail_url)
        self.assertIn('is_thread_follower', response.context)

    def test_view_should_not_render_hidden_thread_for_regular_user(self):
        thread = make_threads(visible=False)
        detail_url = reverse(
            'thread_detail', kwargs={'thread_slug': thread.slug}
        )
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 404)
    
    def test_view_should_not_render_hidden_comment_for_regular_user(self):
        comment = make_comment(self.user, self.thread)
        hidden_comment = make_comment(self.user, self.thread, visible=False)
        response = self.client.get(f"{self.detail_url}")
        self.assertEquals(len(response.context['comments']), 1)
        
        login(self, self.user, 'password')
        response = self.client.get(f"{self.detail_url}")
        self.assertEquals(len(response.context['comments']), 1)

        
    # def test_view_should_render_hidden_comment_for_moderator(self):
    #     comment = make_comment(self.user, self.thread)
    #     hidden_comment = make_comment(self.user, self.thread, visible=False)

    #     login(self, self.user, 'password')
    #     random_user = self.make_user(username="random_testuser")
    #     cat = make_category(title="Random category")
    #     make_moderator(random_user, cat)
    #     response = self.client.get(f"{self.detail_url}")
    #     self.assertEquals(len(response.context['comments']), 1)

    #     make_moderator(self.user, self.thread.category)
    #     response = self.client.get(f"{self.detail_url}")
    #     self.assertEquals(len(response.context['comments']), 2)
        
        

class ThreadUpdateViewTest(ThreadsViewsTest):
    def setUp(self):
        super().setUp()
        self.thread = make_threads(
            1, self.user, self.category, 'python programming', 'hello world'
        )
        self.update_url = reverse(
            'thread_update', kwargs={'thread_slug': self.thread.slug}
        )

    def assert_thread_remain_unchanged(self):
        self.thread.refresh_from_db()
        self.assertEquals(self.thread.category.pk, self.category.pk)
        self.assertEquals(self.thread.title, 'python programming')
        self.assertEquals(self.thread.starting_comment.message, 'hello world')

    def test_anonymous_user_redirect(self):
        """An anonymous user should be redirected to the login page"""
        redirect_url = '%s?next=%s' % (
            reverse('accounts:login'), self.update_url)

        get_response = self.client.get(self.update_url)
        self.assertRedirects(get_response, redirect_url)

        data = {
            'category': self.category.pk,
            'title': 'python programming',
            'message': 'hello word'
        }
        post_response = self.client.post(self.update_url, data)
        self.assertRedirects(post_response, redirect_url)

    def test_authenticated_user_with_no_permission(self):
        """
        Only thread owner can see the thread edit form and update thread
        """
        second_user = self.make_user('testuser2')
        login(self, second_user, 'password')

        get_response = self.client.get(self.update_url)
        self.assertEquals(get_response.status_code, 403)

        data = {
            'category': self.category.pk,
            'title': 'python programming',
            'message': 'hello word'
        }
        post_response = self.client.post(self.update_url, data)
        self.assertEquals(post_response.status_code, 403)

    def test_render_for_authenticated_user_with_permission(self):
        login(self, self.user, 'password')
        response = self.client.get(self.update_url)
        self.assertEquals(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ThreadForm)
    
    def test_view_should_not_render_hidden_thread_for_regular_user(self):
        login(self, self.user, 'password')
        thread = make_threads(visible=False)
        update_url = reverse(
            'thread_detail', kwargs={'thread_slug': thread.slug}
        )
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 404)

    def test_empty_data_rejection(self):
        login(self, self.user, 'password')
        data = {}
        response = self.client.post(self.update_url, data)
        self.assertEquals(response.status_code, 200)
        form = response.context.get('form')
        self.assertTrue(form.errors)

    def test_invalid_data_rejection(self):
        login(self, self.user, 'password')
        data = {
            'category': 'Choose category',
            'title': '',
            'message': '',
        }
        response = self.client.post(self.update_url, data)
        self.assertEquals(response.status_code, 200)
        form = response.context.get('form')
        self.assertTrue(form.errors)

    def test_valid_data_acceptance(self):
        login(self, self.user, 'password')
        data = {
            'category': self.category.pk,
            'title': 'java language specifications',
            'message': 'polymorphism'
        }
        response = self.client.post(self.update_url, data)
        self.assertEquals(response.status_code, 302)
        self.thread.refresh_from_db()
        self.assertEquals(self.thread.category.pk, self.category.pk)
        self.assertEquals(self.thread.title, 'java language specifications')
        self.assertEquals(self.thread.starting_comment.message, 'polymorphism')

    def test_view_should_not_allow_post_for_hidden_thread(self):
        thread = make_threads(
            user=self.user, category=self.category, 
            title='python programming 23', message='hello world 23', 
            visible=False
        )        
        login(self, self.user, 'password')
        data = {
            'category': self.category.pk,
            'title': 'java language specifications',
            'message': 'polymorphism'
        }
        update_url = reverse(
            'thread_update', kwargs={'thread_slug': thread.slug}
        )
        
        update_hidden_url = f'{update_url}'
        response = self.client.post(update_hidden_url, data)
        self.assertEquals(response.status_code, 404)
        
        thread.refresh_from_db()
        self.assertEquals(thread.category.pk, self.category.pk)
        self.assertEquals(thread.title, 'python programming 23')
        self.assertEquals(thread.starting_comment.message, 'hello world 23')

    def test_view_should_prevent_moderators_from_posting(self):
        thread = make_threads(
            user=self.user, category=self.category, 
            title='python programming 23', message='hello world 23', 
            visible=False
        )        
        make_moderator(self.user, thread.category)
        login(self, self.user, 'password')
        data = {
            'category': self.category.pk,
            'title': 'java language specifications',
            'message': 'polymorphism'
        }
        update_url = reverse(
            'thread_update', kwargs={'thread_slug': thread.slug}
        )
        update_hidden_url = f'{update_url}'
        response = self.client.post(update_hidden_url, data)
        self.assertEquals(response.status_code, 403)
        
        thread.refresh_from_db()
        self.assertEquals(thread.category.pk, self.category.pk)
        self.assertEquals(thread.title, 'python programming 23')
        self.assertEquals(thread.starting_comment.message, 'hello world 23')

    def test_category_cannot_be_changed(self):
        login(self, self.user, 'password')
        second_category = make_category(title='second_category')
        data = {
            'category': second_category.pk,
            'title': 'java language specifications',
            'message': 'polymorphism'
        }
        response = self.client.post(self.update_url, data)
        self.assertEquals(response.status_code, 302)
        self.thread.refresh_from_db()
        self.assertEquals(self.thread.category.pk, self.category.pk)
        self.assertEquals(self.thread.title, 'java language specifications')
        self.assertEquals(self.thread.starting_comment.message, 'polymorphism')


class FollowThreadViewTest(ThreadsViewsTest):
    def setUp(self):
        super().setUp()
        self.thread = make_threads(
            count=1, user=self.user, category=self.category
        )
        self.follow_url = reverse(
            'thread_follow', kwargs={'thread_slug': self.thread.slug}
        )

    def test_anonymous_user_redirect(self):
        """An anonymous user should be redirected to the login page"""
        redirect_url = '%s?next=%s' % (
            reverse('accounts:login'), self.follow_url)

        response = self.client.post(self.follow_url)
        self.assertRedirects(response, redirect_url)

    def test_submit_success_for_authenticated_user(self):
        current_count = self.thread.followers.count()
        second_user = self.make_user('testuser2')
        login(self, second_user, 'password')
        response = self.client.post(self.follow_url)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.thread.followers.count(), current_count + 1)
