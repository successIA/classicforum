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


class ThreadCreateTest(TestCase):
    def setUp(self):
        testutils.sign_up_a_new_user(self, 'john')
        self.user = User.objects.get(id=1)
        self.category = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='django')
        self.response = self.client.get(self.category.get_thread_create_url())

        self.img_file = SimpleUploadedFile(name='test_image.jpg', content=open(image_path, 'rb').read(), content_type='image/jpeg')

        self.img_file2 = SimpleUploadedFile(name='test_image2.jpg', content=open(image_path2, 'rb').read(), content_type='image/jpeg')
        # img_file2 = SimpleUploadedFile(name='test_image2.jpg', content=open(image_path, 'rb').read(), content_type='image/jpeg')
        # Image.objects.create(content_object=self.thread, image=img_file)
        # Image.objects.create(content_object=self.thread, image=img_file2)

    def test_an_authenticated_user_can_create_threads(self):
        response = self.client.post(self.category.get_thread_create_url(), {'title': 'Galaxy S5 Discussion Thread', 'body': 'Lorem ipsum dalor'}, follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(Thread.objects.filter(title='Galaxy S5 Discussion Thread').exists())

    def test_an_unauthenticated_user_cannot_create_threads(self):
        self.client.logout()
        response = self.client.post(self.category.get_thread_create_url(), {'title': 'Galaxy S5 Discussion Thread', 'body': 'Lorem ipsum dalor'}, follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertFalse(Thread.objects.filter(title='Galaxy S5 Discussion Thread').exists())

    def test_thread_form_contains_enctype(self):
        self.assertContains(self.response, 'enctype="multipart/form-data"')

    def test_thread_form_context_fields(self):
        self.assertContains(self.response, '<input', 8)
        self.assertContains(self.response, 'type="file"', 5)
        fields = ['title', 'body', 'image_set1', 'image_set2', 'image_set3', 'image_set4', 'image_set5']
        self.assertTrue(self.response.context.get('form'))
        self.assertEquals(fields, list(self.response.context.get('form').fields))

    def test_an_authenticated_user_can_create_a_thread_with_images(self):
        # send post data of thread and image
        response = self.client.post(self.category.get_thread_create_url(), {'title': 'Galaxy S5 Discussion Thread', 'body': 'Lorem ipsum dalor', 'image_set1': self.img_file, 'image_set2': self.img_file2}, follow=True)
        # retrive the same thread from the db to new values
        thread = Thread.objects.get(id=1)

        self.assertEquals(response.status_code, 200)
        '''
        Retrieve the inserted thread's images from database
        '''
        thread = Thread.objects.get(id=1)
        image_obj = thread.images.first()
        image = image_obj.image
        image_obj2 = thread.images.get(id=2)
        image2 = image_obj2.image

        # build the image path of the images
        img_path = os.path.join(img_dir, image.path)
        img_path2 = os.path.join(img_dir, image2.path)

        # extract the image path of the image
        name = image.name.split('/')[2]
        name2 = image2.name.split('/')[2]

        # build a SimpleUploadedFile object with the images' name and images' path
        uploaded_image = SimpleUploadedFile(name=name, content=open(img_path, 'rb').read(), content_type='image/jpeg')
        uploaded_image2 = SimpleUploadedFile(name=name2, content=open(img_path2, 'rb').read(), content_type='image/jpeg')

        # delete the images from the file system
        image_obj.image.delete()
        image_obj2.image.delete()

        # delete image from the image table
        image_obj.delete()
        image_obj2.delete()

        self.assertEquals(uploaded_image.size, self.img_file.size)
        self.assertEquals(uploaded_image.name, self.img_file.name)

        self.assertEquals(uploaded_image2.size, self.img_file2.size)
        self.assertEquals(uploaded_image2.name, self.img_file2.name)
