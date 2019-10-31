import datetime
import os

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve, reverse
from django.core.files.uploadedfile import SimpleUploadedFile


from forum.accounts.forms import UserSignUpForm
from forum.accounts.views import SignUpView
from forum.accounts.models import UserProfile

from forum.accounts.views import UserProfileView

from forum.categories.models import Category
from forum.threads.models import Thread

from forum import testutils


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath('__file__')))

image_path = os.path.join(BASE_DIR, 'forum_project', 'forum', 'accounts', 'tests', 'images', 'marketing1.jpg')

img_dir = os.path.join(BASE_DIR, 'forum_project', 'forum', 'media')


class SignUpInit(TestCase):
    def setUp(self):
        testutils.sign_up_a_new_user(self, 'john')
        self.user = User.objects.get(id=1)
        self.userprofile = self.user.userprofile
        self.response = self.client.get(self.userprofile.get_absolute_url())
        self.category = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='django')
        self.thread = Thread.objects.create(title='Galaxy S5 Discussion Thread', body='Lorem ipsum dalor', category=self.category, user=self.user)
        self.img_file = SimpleUploadedFile(name='test_userprofile_pic.jpg', content=open(image_path, 'rb').read(), content_type='image/jpeg')


class UserProfileUpdateViewTest(SignUpInit):

    def test_a_can_add_profile_picture(self):
        response = self.client.post(self.userprofile.get_userprofile_update_url(), {'image': self.img_file}, follow=True)
        self.assertEquals(response.status_code, 200)
        print('response: ', response.context.get('form'))
        self.assertTemplateUsed('user_profile.html')
        '''
        Retrieve the inserted userprofile's picture from database
        '''
        userprofile = UserProfile.objects.get(id=1)

        image_obj = userprofile.images.first()
        image = image_obj.image

        # build the image path of the image
        img_path = os.path.join(img_dir, image.path)

        # extract the name of the image
        name = image.name.split('/')[2]

        # build a SimpleUploadedFile object with the images' name and images' path
        uploaded_image = SimpleUploadedFile(name=name, content=open(img_path, 'rb').read(), content_type='image/jpeg')

        # delete the images from the file system
        image_obj.image.delete()

        # delete image from the image table
        image_obj.delete()

        self.assertEquals(uploaded_image.size, self.img_file.size)
        self.assertEquals(uploaded_image.name, self.img_file.name)

    def test_thread_form_contains_enctype(self):
        self.assertContains(self.response, 'enctype="multipart/form-data"')

    def test_thread_form_context_fields(self):
        self.assertContains(self.response, '<input', 3)
        self.assertContains(self.response, 'type="file"', 1)
        fields = ['image']
        self.assertTrue(self.response.context.get('form'))
        self.assertEquals(fields, list(self.response.context.get('form').fields))

    def test_profile_update_with_invalid_data(self):
        response = self.client.post(self.userprofile.get_userprofile_update_url(), {'image': {}}, follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertNotEqual(response.context.get('form').errors, None)

    def test_profile_update_with_visitor(self):
        self.client.logout()
        response = self.client.post(self.userprofile.get_userprofile_update_url(), {'image': {}}, follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed('login.html')
    # def test_profile_update_with_unpermitted_user(self):
