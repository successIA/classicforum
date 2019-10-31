# from django.core.urlresolvers import reverse, resolve
# from django.test.client import RequestFactory
from django.test import TestCase
from django.contrib.auth.models import User

from forum.categories.models import Category, create_category_slug
from forum.threads.models import Thread, create_thread_slug
from forum.accounts.models import UserProfile


class ModelSlugCategoryTest(TestCase):
    def test_create_category_slug_without_slug(self):
        category = Category(title='Django', description='The Web Framework For The Perfectionist')
        slug = create_category_slug(category)
        self.assertEquals(slug, 'django')

    def test_create_category_slug_with_valid_slug(self):
        category = Category(title='Django', description='The Web Framework For The Perfectionist', slug='django-devt')
        slug = create_category_slug(category)
        self.assertEquals(slug, 'django-devt')

    def test_create_category_slug_with_empty_slug(self):
        category = Category(title='Django', description='The Web Framework For The Perfectionist', slug=None)
        slug = create_category_slug(category)
        self.assertTrue(slug)
        self.assertEquals(slug, 'django')

    def test_create_category_slug_with_invalid_slug(self):
        category = Category(title='Django', description='The Web Framework For The Perfectionist', slug='Th?-*')
        slug = create_category_slug(category)
        self.assertEquals(slug, 'th-')


class ModelSlugThreadTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='john', email='john@example.com', password='pass1234')
        self.category = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='django')

    def test_create_thread_slug_without_slug(self):
        thread = Thread(title='Galaxy S5 Discussion Thread', body='Lorem ipsum dalor', category=self.category, user=self.user)
        slug = create_thread_slug(thread)
        self.assertEquals(slug, 'galaxy-s5-discussion-thread')

    def test_create_thread_slug_with_valid_slug(self):
        thread = Thread(title='Galaxy S5 Discussion Thread', slug='galaxy-s5-discussion-thread', body='Lorem ipsum dalor', category=self.category, user=self.user)
        slug = create_thread_slug(thread)
        self.assertEquals(slug, 'galaxy-s5-discussion-thread')

    def test_create_thread_slug_with_empty_slug(self):
        thread = Thread(title='Galaxy S5 Discussion Thread', slug='', body='Lorem ipsum dalor', category=self.category, user=self.user)
        slug = create_thread_slug(thread)
        self.assertTrue(slug)
        self.assertEquals(slug, 'galaxy-s5-discussion-thread')

    def test_create_thread_slug_with_invalid_slug(self):
        thread = Thread(title='Galaxy S5 Discussion Thread', slug='Th?-*', body='Lorem ipsum dalor', category=self.category, user=self.user)
        slug = create_thread_slug(thread)
        self.assertEquals(slug, 'th-')


class ModelCategorySignalReceiverTest(TestCase):
    def test_signal_derives_category_slug_field_without_slug(self):
        category = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist')
        self.assertEquals(category.slug, 'django')

    def test_signal_uses_the_given_slug(self):
        category = Category.objects.create(title='Django', slug='django-devt', description='The Web Framework For The Perfectionist')
        self.assertEquals(category.slug, 'django-devt')

    def test_signal_slug_correct_invalid_slug(self):
        category = Category(title='Django', description='The Web Framework For The Perfectionist', slug='Th?-*')
        category.save()
        self.assertEquals(category.slug, 'th-')

    def test_signal_does_not_save_the_same_slug_for_two_categories_having_the_same_slug(self):
        category1 = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='Th?-*')
        category2 = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='Th?-*')
        self.assertNotEquals(category1.slug, category2.slug)


class ModelThreadSignalReceiverTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='john', email='john@example.com', password='pass1234')
        self.userprofile = UserProfile.objects.create(user=self.user) 
        self.category = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='django')

    def test_signal_derives_thread_slug_field_without_slug(self):
        thread = Thread.objects.create(title='Galaxy S5 Discussion Thread', body='Lorem ipsum dalor', category=self.category, user=self.user)
        self.assertEquals(thread.slug, 'galaxy-s5-discussion-thread')

    def test_signal_uses_the_given_slug(self):
        thread = Thread.objects.create(title='Galaxy S5 Discussion Thread', slug='galaxy-s5-discussion-thread', body='Lorem ipsum dalor', category=self.category, user=self.user)
        self.assertEquals(thread.slug, 'galaxy-s5-discussion-thread')

    def test_signal_does_not_save_the_same_slug_for_two_threads_having_the_same_slug(self):
        thread1 = Thread.objects.create(title='Galaxy S5 Discussion Thread', slug='Th?-*', body='Lorem ipsum dalor', category=self.category, user=self.user)
        thread2 = Thread.objects.create(title='Galaxy S5 Discussion Thread', slug='Th?-*', body='Lorem ipsum dalor', category=self.category, user=self.user)
        self.assertNotEquals(thread2.slug, thread1.slug)
