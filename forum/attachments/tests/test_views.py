from django.core.urlresolvers import reverse, resolve
from django.test.client import RequestFactory
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings
from django.http import JsonResponse
from django.conf import settings

from forum.categories.models import Category
from forum.threads.models import Thread
from forum.threads.views import ThreadDetailView
from forum.comments.models import Comment
from forum.accounts.models import UserProfile
from forum.attachments.models import Attachment
from forum.attachments.utils import md5

from forum import testutils

import os
import tempfile
from PIL import Image
import glob
import shutil


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath('__file__')))

image_path = os.path.join(BASE_DIR, 'forum_project', 'forum','threads',
                         'tests', 'images', 'marketing1.jpg')

image_path2 = os.path.join(BASE_DIR, 'forum_project', 'forum','threads',
                          'tests', 'images', 'abu3.jpg')

image_path3 = os.path.join(BASE_DIR, 'forum_project', 'forum','attachments',
                          'tests', 'images', 'marketing1.jpg')

image_path4 = os.path.join(BASE_DIR, 'forum_project', 'forum','attachments',
                          'tests', 'images', 'marketing1_fake.jpg')

image_path5 = os.path.join(BASE_DIR, 'forum_project', 'forum','attachments',
                          'tests', 'images', 'non_image.txt')

image_path6 = os.path.join(BASE_DIR, 'forum_project', 'forum','attachments',
                          'tests', 'images', '15.jpg')

img_dir = os.path.join(BASE_DIR, 'forum_project', 'forum', 'media', 'tests')

settings.MEDIA_ROOT = img_dir
# settings.MEDIA_URL = '/media_test/'

def get_temp_img():
    size = (200, 200)
    color = (255, 0, 0, 0)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        image = Image.new("RGB", size, color)
        image.save(f, "PNG")
    return open(f.name, mode="rb")


class AttachmentViewsTest(TestCase):
    # @override_settings(MEDIA_ROOT=img_dir)
    def setUp(self):
        testutils.sign_up_a_new_user(self, 'john')
        self.user = User.objects.get(id=1)
        self.category = Category.objects.create(
                            title='Django',
                            description='The Web Framework For The Perfectionist',
                            slug='django'
                        )
        self.thread = Thread.objects.create(
                        title='Galaxy S5 Discussion Thread',
                        body='Lorem ipsum dalor',
                        category=self.category,
                        user=self.user
                    )
        self.comment = Comment.objects.create(
                            message='python is awesome',
                            thread=self.thread,
                            user=self.user
                        )
        self.image = SimpleUploadedFile(
                            name='test_image.jpg',
                            content=open(image_path, 'rb').read(),
                            content_type='image/jpeg'
                            )

        self.response = self.client.post(reverse('attachments:upload_img'), 
                                     {'image': self.image}, 
                                     HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        # self.test_image = get_temp_img()

    def tearDown(self):        
        # img_path = os.path.join(img_dir, md5(self.image) + '.jpg')
        # # self.test_image.close()
        # if os.path.exists(img_path):
        #     os.remove(img_path)
        folder = os.path.join(img_dir, 'uploads')
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except Exception as e:
                print(e)


    def test_upload_view_for_authenticated_user(self):
        self.assertEquals(self.response.status_code, 200)
        attachment_qs = Attachment.objects.filter(id=1)
        self.assertTrue(attachment_qs.exists())
        attachment = attachment_qs.first()
        self.assertIsInstance(attachment, Attachment)
        self.assertEquals(attachment.filename, 'test_image.jpg')
        # self.assertEquals(attachment.url, '/media/tests/uploads/' + attachment.md5sum + '.jpg')
        self.assertTrue(attachment.is_orphaned)
        self.assertEquals(attachment.md5sum, md5(self.image))
        # print(dir(attachment.image.file))
        # self.assertTrue(os.path.exists(attachment.image.file))
        # path, dirs, files = os.walk(img_dir).__next__()
        # file_count = len(files)
        # number_of_files = len([item for item in os.listdir(img_dir) if os.path.isfile(os.path.join(img_dir, item))])

        # self.assertEquals(number_of_files, 1)

    def test_upload_view_for_unauthenticated_user(self):
        self.client.logout()
        attachment = Attachment.objects.get(id=1)
        attachment.delete()
        self.assertEquals(Attachment.objects.all().count(), 0)
        response = self.client.post(reverse('attachments:upload_img'), 
                                     {'image': self.image}, 
                                     HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Attachment.objects.all().count(), 0)
        path, dirs, files = next(os.walk(img_dir))
        file_count = len(files)
        self.assertEquals(file_count, 0)

    def test_upload_view_response_for_get(self):
        response = self.client.get(reverse('attachments:upload_img'))
        self.assertEquals(response.status_code, 302)
  
    def test_upload_view_response_for_post(self):
        self.assertEquals(self.response.status_code, 200)
        self.assertEquals(type(self.response), JsonResponse)
        data = self.response.json()
        self.assertTrue(data['is_valid'])
        self.assertEquals(data['name'], 'uploads/' + md5(self.image) + '.jpg')
        # self.assertEquals(data['url'], 'media/tests/uploads/' + md5(self.image) + '.jpg')

    def test_upload_view_for_duplicate_images(self):
        img = SimpleUploadedFile(name='test_image.jpg',
                                 content=open(image_path, 'rb').read(),
                                 content_type='image/jpeg')

        self.client.post(reverse('attachments:upload_img'), 
                                 {'image': img}, 
                                 HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEquals(Attachment.objects.all().count(), 1) 
        data = self.response.json()
        self.assertTrue(data['is_valid'])
        self.assertEquals(data['name'], 'uploads/' + md5(self.image) + '.jpg')
        # self.assertEquals(data['url'], 'media/tests/uploads/' + md5(self.image) + '.jpg')

    def test_upload_view_for_another_image(self):
        img2 = SimpleUploadedFile(name='test_image2.jpg',
                                  content=open(image_path2, 'rb').read(),
                                  content_type='image/jpeg')

        response = self.client.post(reverse('attachments:upload_img'), 
                                    {'image': img2}, 
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEquals(self.response.status_code, 200)
        attachment_qs2 = Attachment.objects.filter(id=2)
        self.assertTrue(attachment_qs2.exists())
        attachment = attachment_qs2.first()
        self.assertIsInstance(attachment, Attachment)
        self.assertEquals(attachment.filename, 'test_image2.jpg')
        # self.assertEquals(attachment.url, '/media/tests/uploads/' + attachment.md5sum + '.jpg')
        self.assertTrue(attachment.is_orphaned)
        self.assertEquals(attachment.md5sum, md5(img2))
        # self.assertTrue(os.path.exists(attachment.image))
        # path, dirs, files = next(os.walk(img_dir))
        # file_count = len(files)
        # self.assertEquals(file_count, 2)

    def test_upload_view_for_image_with_same_name_diff_file(self):
        img = SimpleUploadedFile(name='test_image.jpg',
                                content=open(image_path3, 'rb').read(),
                                content_type='image/jpeg')

        response = self.client.post(reverse('attachments:upload_img'), 
                                     {'image': img}, 
                                     HTTP_X_REQUESTED_WITH='XMLHttpRequest')  
        self.assertEquals(self.response.status_code, 200)
        attachment_qs2 = Attachment.objects.filter(id=2)
        self.assertTrue(attachment_qs2.exists())
        attachment = attachment_qs2.first()
        self.assertIsInstance(attachment, Attachment)
        self.assertEquals(attachment.filename, 'test_image.jpg')
        # self.assertEquals(attachment.url, '/media/tests/uploads/' + attachment.md5sum + '.jpg')
        self.assertTrue(attachment.is_orphaned)
        self.assertEquals(attachment.md5sum, md5(img))
        # self.assertTrue(os.path.exists(attachment.image))
        # path, dirs, files = next(os.walk(img_dir))
        # file_count = len(files)
        # self.assertEquals(file_count, 2)


    def test_upload_view_for_image_with_diff_name_same_file(self):
        img = SimpleUploadedFile(name='test_image2.jpg',
                                content=open(image_path4, 'rb').read(),
                                content_type='image/jpeg')

        response = self.client.post(reverse('attachments:upload_img'), 
                                     {'image': img}, 
                                     HTTP_X_REQUESTED_WITH='XMLHttpRequest') 

        self.assertEquals(Attachment.objects.all().count(), 1) 
        data = self.response.json()
        self.assertTrue(data['is_valid'])
        self.assertEquals(data['name'], 'uploads/' + md5(img) + '.jpg')
        # self.assertEquals(data['url'], 'media/tests/uploads/' + md5(self.image) + '.jpg')

    def test_upload_view_for_non_image(self):
        img = SimpleUploadedFile(name='test_image2.jpg',
                                content=open(image_path5, 'rb').read(),
                                content_type='image/jpeg')

        response = self.client.post(reverse('attachments:upload_img'), 
                                     {'image': img}, 
                                     HTTP_X_REQUESTED_WITH='XMLHttpRequest') 
        self.assertEquals(Attachment.objects.all().count(), 1) 
        data = response.json()
        self.assertFalse(data['is_valid'])


    def test_upload_view_with_image_above_upload_size(self):
        img = SimpleUploadedFile(name='test_image2.jpg',
                                content=open(image_path6, 'rb').read(),
                                content_type='image/jpeg')

        response = self.client.post(reverse('attachments:upload_img'), 
                                     {'image': img}, 
                                     HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(type(self.response), JsonResponse)                                      
        self.assertEquals(Attachment.objects.all().count(), 1) 
        data = response.json()
        print(data['message'])
        self.assertFalse(data['is_valid'])


