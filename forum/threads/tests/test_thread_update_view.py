from django.core.urlresolvers import reverse, resolve
from django.test.client import RequestFactory
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from forum.categories.models import Category
from forum.threads.models import Thread
from forum.threads.views import ThreadDetailView
from forum.comments.models import Comment
from forum.image_app.models import Image

from forum import testutils

import os


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath('__file__')))
image_path = os.path.join(BASE_DIR, 'forum_project', 'forum','threads', 'tests', 'images', 'marketing1.jpg')
image_path2 = os.path.join(BASE_DIR, 'forum_project', 'forum','threads', 'tests', 'images', 'abu3.jpg')

img_dir = os.path.join(BASE_DIR, 'forum_project', 'forum', 'media')


class ThreadUpdateTest(TestCase):
    def setUp(self):
        testutils.sign_up_a_new_user(self, 'john')
        self.user = User.objects.get(id=1)
        self.category = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='django')
        self.thread = Thread.objects.create(title='Galaxy S5 Discussion Thread', body='Lorem ipsum dalor', category=self.category, user=self.user)
        self.response = self.client.get(self.thread.get_thread_update_url())

        self.img_file = SimpleUploadedFile(name='test_image.jpg', content=open(image_path, 'rb').read(), content_type='image/jpeg')

        self.img_file2 = SimpleUploadedFile(name='test_image2.jpg', content=open(image_path2, 'rb').read(), content_type='image/jpeg')
        self.img_file3 = SimpleUploadedFile(name='test_image3.jpg', content=open(image_path2, 'rb').read(), content_type='image/jpeg')
        # img_file2 = SimpleUploadedFile(name='test_image2.jpg', content=open(image_path, 'rb').read(), content_type='image/jpeg')
        # Image.objects.create(content_object=self.thread, image=img_file)
        # Image.objects.create(content_object=self.thread, image=img_file2)

    def test_an_authenticated_user_can_see_thread_update_form(self):
        self.assertEquals(self.response.status_code, 200)

    def test_an_authenticated_user_can_update_a_thread(self):
        response = self.client.post(self.thread.get_thread_update_url(), {'title': 'Galaxy S8 Discussion Thread', 'body': 'Lorem ipsum dalor'}, follow=True)
        self.assertEquals(response.status_code, 200)
        thread = Thread.objects.filter(title=self.thread.title).first()
        self.assertEquals(thread, None)
        thread2 = Thread.objects.filter(title='Galaxy S8 Discussion Thread').first()
        self.assertEquals(thread2.title, 'Galaxy S8 Discussion Thread')

    def test_an_unauthenticated_user_cannot_update_threads(self):
        self.client.logout()
        response = self.client.post(self.thread.get_thread_update_url(), {'title': 'Galaxy S7 Discussion Thread', 'body': 'Lorem ipsum dalor'}, follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertFalse(Thread.objects.filter(title='Galaxy S7 Discussion Thread').exists())

    def test_thread_slug_remain_unchanged_after_update(self):
        self.client.post(self.thread.get_thread_update_url(), {'title': 'Galaxy S5 Discussion Thread', 'body': 'Lorem ipsum dalor'})
        slug = 'galaxy-s5-discussion-thread'
        self.assertEquals(slug, self.thread.slug)

    def test_thread_form_contains_enctype(self):
        self.assertContains(self.response, 'enctype="multipart/form-data"')

    def test_thread_form_context_fields(self):
        self.assertContains(self.response, '<input', 9)
        self.assertContains(self.response, 'type="file"', 5)
        fields = ['title', 'body', 'image_set1', 'image_set2', 'image_set3', 'image_set4', 'image_set5']
        self.assertTrue(self.response.context.get('form'))
        self.assertEquals(fields, list(self.response.context.get('form').fields))

