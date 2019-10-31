from django.core.urlresolvers import reverse, resolve
from django.test.client import RequestFactory
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings

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


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath('__file__')))

image_path = os.path.join(BASE_DIR, 'forum_project', 'forum','threads',
                         'tests', 'images', 'marketing1.jpg')

image_path2 = os.path.join(BASE_DIR, 'forum_project', 'forum','threads',
                          'tests', 'images', 'abu3.jpg')

img_dir = os.path.join(BASE_DIR, 'forum_project', 'forum', 'media', 'tests')


def get_temp_img():
    size = (200, 200)
    color = (255, 0, 0, 0)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        image = Image.new("RGB", size, color)
        image.save(f, "PNG")
    return open(f.name, mode="rb")


class AttachmentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='John', password='pass1234')
        self.userprofile = UserProfile.objects.create(user=self.user)
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

    # @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_attachment_creation(self):
        attachment = Attachment(image=self.image)

        # Use instance.save instead of Class.objects.create to avoid
        # unique constraint error
        attachment.save()
        self.assertIsNotNone(attachment)
        attachment_qs_db = Attachment.objects.filter(id=1)
        self.assertTrue(attachment_qs_db.exists())
        self.assertIsInstance(attachment, Attachment)
        self.assertEquals(attachment, attachment_qs_db.first())
        self.assertEquals(attachment.filename, 'test_image.jpg')
        # self.assertEquals(attachment.url, '/media/tests/uploads/' + attachment.md5sum + '.jpg')
        self.assertTrue(attachment.is_orphaned)
        self.assertEquals(attachment.md5sum, md5(self.image))







        # self.assertEquals(attachment.filename, '')
        # attachment.image.delete()
        # img_path = os.path.join(img_dir, image.path)
        # name = image.name.split('/')[2]
        # uploaded_image = SimpleUploadedFile(
        #                     name=name, 
        #                     content=open(img_path, 'rb').read(), 
        #                     content_type='image/jpeg'
        #                 )

       # delete the uploaded file from the media directory
       # attachment.image.delete()  
       # attachment.delete()
       # self.assertEquals(uploaded_image.size, self.image.size)








