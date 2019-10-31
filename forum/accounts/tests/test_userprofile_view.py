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

import datetime

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath('__file__')))

image_path = os.path.join(BASE_DIR, 'forum_project', 'forum', 'accounts', 'tests', 'images', 'marketing1.jpg')

img_dir = os.path.join(BASE_DIR, 'forum_project', 'forum', 'media')


class SignUpTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='john', email='john@example.com', password='pass1234')
        self.userprofile = UserProfile.objects.create(user=self.user)
        self.response = self.client.get(self.userprofile.get_absolute_url())
        self.category = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='django')
        self.thread = Thread.objects.create(title='Galaxy S5 Discussion Thread', body='Lorem ipsum dalor', category=self.category, user=self.user)
        self.img_file = SimpleUploadedFile(name='test_image.jpg', content=open(image_path, 'rb').read(), content_type='image/jpeg')

    def test_userprofile_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_signup_url_resolves_signup_view(self):
        view = resolve(self.userprofile.get_absolute_url())
        self.assertEquals(view.func.view_class, UserProfileView)

    def test_userprofile_page_may_have_a_userprofile_context(self):
        self.assertEquals(self.response.context.get('userprofile'), self.userprofile)

    # def test_userprofile_page_may_have_a_followed_threads_context(self):
        # '''
        # todo: queryset equality issue
        # '''
    #     self.userprofile.followed_threads.add(self.thread)
    #     response = self.client.get(self.userprofile.get_absolute_url())
    #     self.assertEqual(response.context['followed_threads'], self.userprofile.followed_threads.all())

    # def test_userprofile_page_may_not_have_a_followed_threads_context(self):
        # '''
        # todo: queryset equality issue
        # '''
    #     response = self.client.get(self.userprofile.get_absolute_url())
    #
    #     self.assertEqual(response.context['followed_threads'], self.userprofile.followed_threads.all())

    def test_userprofile_page_may_have_a_username_context(self):
        self.assertEqual(self.response.context['username'], self.userprofile.user.username)


class UserFollowTest(TestCase):
    def setUp(self):
        url = reverse('signup')
        data = {
            'username': 'john',
            'email': 'john@doe.com',
            'password1': 'abcdef123456',
            'password2': 'abcdef123456'
        }
        self.response = self.client.post(url, data)

        self.user1 = User.objects.get(id=1)

        self.user2 = User.objects.create_user(username='janet', email='janet@example.com', password='pass1234')
        self.userprofile2 = UserProfile.objects.create(user=self.user2)
        # self.client.login(username=self.user1.username, password=self.user1.password)

    def test_user2_can_follow_user1(self):
        self.user1.userprofile.followers.add(self.user2)
        self.assertEquals(self.user1.userprofile.followers.first(), self.user2)

    def test_user_follow_view(self):
        response = self.client.get(self.userprofile2.get_user_follow_url())
        print(self.user1.userprofile.followers.all())
        self.assertEquals(self.user1.userprofile.followers.first(), self.user2)
        self.assertEquals(response.status_code, 302)

    def test_user_cannot_follow_self(self):
        response = self.client.get(self.user1.userprofile.get_user_follow_url())
        self.assertNotEquals(self.user1.userprofile.followers.first(), self.user1)
        self.assertEquals(response.status_code, 404)

    def test_visitor_redirect(self):
        self.client.logout()
        response = self.client.get(self.userprofile2.get_user_follow_url())
        self.assertEquals(self.user1.userprofile.followers.first(), None)
        self.assertEquals(response.status_code, 302)
