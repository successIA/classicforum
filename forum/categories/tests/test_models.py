# from django.core.urlresolvers import reverse, resolve
# from django.test.client import RequestFactory
from django.test import TestCase
from django.contrib.auth.models import User

from forum.categories.models import Category, create_category_slug
from forum.threads.models import Thread, create_thread_slug


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
