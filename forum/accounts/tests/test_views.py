import os
import shutil
from datetime import timedelta

from django.conf import settings
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.test import Client, RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from faker import Faker
from test_plus import TestCase

from forum.accounts.forms import UserProfileForm
from forum.accounts.models import User
from forum.accounts.tests.utils import login
from forum.accounts.tokens import account_activation_token
from forum.attachments.models import Attachment
from forum.comments.models import CommentQuerySet
from forum.notifications.models import Notification
from forum.threads.models import ThreadQuerySet

fake = Faker()

TEST_AVATARS_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'testavatars'
)
TEST_AVATAR_1 = os.path.join(TEST_AVATARS_DIR, 'aprf1.jpg')
TEST_AVATAR_1_COPY = os.path.join(TEST_AVATARS_DIR, 'aprf1_copy.jpg')
TEST_AVATAR_LARGE = os.path.join(TEST_AVATARS_DIR, 'Chrysanthemum.jpg')


class UserProfileStatsViewTest(TestCase):
    def test_stats(self):
        user = self.make_user('testuser1')
        url = reverse(
            'accounts:user_stats', kwargs={'username': user.username}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['userprofile'], user)
        self.assertEqual(response.context['current_profile_page'], 'stats')
        self.assertIn('comment_count', response.context)
        self.assertIn('followers', response.context)
        self.assertIn('following', response.context)
        self.assertIn('last_posted', response.context)
        self.assertIn('active_category', response.context)
        self.assertIn('total_likes', response.context)
        self.assertIn('total_liked', response.context)
        self.assertIsInstance(
            response.context['recent_comments'], CommentQuerySet
        )
        self.assertIsInstance(
            response.context['recent_threads'], ThreadQuerySet
        )


class UserNotificationList(TestCase):
    def setUp(self):
        self.user = self.make_user('testuser1')
        self.notif_url = reverse(
            'accounts:user_notifs', kwargs={'username': self.user.username}
        )

    def test_anonymous_user_redirect(self):
        """An anonymous user should be redirected to the login page"""
        redirect_url = '%s?next=%s' % (
            reverse('accounts:login'), self.notif_url
        )
        response = self.client.get(self.notif_url)
        self.assertRedirects(response, redirect_url)

    def test_authenticated_user_with_no_permission(self):
        """
        Only comment owner can see the comment edit form and update comment
        """
        second_user = self.make_user('testuser2')
        login(self, second_user, 'password')
        response = self.client.get(self.notif_url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_user_with_permission(self):
        login(self, self.user, 'password')
        response = self.client.get(self.notif_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['userprofile'], self.user)
        self.assertEqual(
            response.context['current_profile_page'], 'user_notifs')
        self.assertIsInstance(response.context['notifications'], Page)


@override_settings(MEDIA_ROOT=settings.TEST_MEDIA_ROOT)
class UserProfileEditTest(TestCase):
    def setUp(self):
        self.user = self.make_user('testuser1')
        self.user_edit_url = reverse(
            'accounts:user_edit', kwargs={'username': self.user.username}
        )
        self.test_avatar = SimpleUploadedFile(
            name='aprf1.jpg',
            content=open(TEST_AVATAR_1, 'rb').read(),
            content_type='image/jpeg'
        )
        self.test_avatar_copy = SimpleUploadedFile(
            name='aprf1_copy.jpg',
            content=open(TEST_AVATAR_1_COPY, 'rb').read(),
            content_type='image/jpeg'
        )
        self.test_avatar_large = SimpleUploadedFile(
            name='Chrysanthemum.jpg',
            content=open(TEST_AVATAR_LARGE, 'rb').read(),
            content_type='image/jpeg'
        )
        self.valid_data = {
            'image': self.test_avatar,
            'gender': 'M',
            'signature': 'This is a test signature',
            'location': 'This is a test location',
            'website': 'http://www.example.com'
        }

    def tearDown(self):
        self.test_avatar.close()
        self.test_avatar_copy.close()
        self.test_avatar_large.close()
        try:
            if os.path.isdir(settings.TEST_MEDIA_ROOT):
                shutil.rmtree(settings.TEST_MEDIA_ROOT)
        except Exception as e:
            print(e)

    def test_anonymous_user_redirect(self):
        """An anonymous user should be redirected to the login page"""
        redirect_url = '%s?next=%s' % (
            reverse('accounts:login'), self.user_edit_url
        )
        get_response = self.client.get(self.user_edit_url)
        self.assertRedirects(get_response, redirect_url)

        post_response = self.client.post(self.user_edit_url, self.valid_data)
        self.assertRedirects(post_response, redirect_url)

    def test_authenticated_user_with_no_permission(self):
        """
        Only comment owner can see the comment edit form and update comment
        """
        redirect_url = '%s?next=%s' % (
            reverse('accounts:login'), self.user_edit_url
        )
        second_user = self.make_user('testuser2')
        login(self, second_user.username, 'password')
        get_response = self.client.get(self.user_edit_url)
        self.assertEqual(get_response.status_code, 403)

        post_response = self.client.post(self.user_edit_url, self.valid_data)
        self.assertEqual(post_response.status_code, 403)

    def test_render_for_authenticated_user_with_permission(self):
        login(self, self.user.username, 'password')
        response = self.client.get(self.user_edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['userprofile'], self.user)
        self.assertEqual(
            response.context['current_profile_page'], 'settings')
        self.assertIsInstance(response.context['form'], UserProfileForm)

    def test_large_image(self):
        login(self, self.user, 'password')
        self.valid_data.update({'image': self.test_avatar_large})
        data = self.valid_data
        with self.settings(DEBUG=True):
            response = self.client.post(self.user_edit_url, data)
        self.assertEqual(response.status_code, 200)
        message = 'File too large. Size should not exceed 500 KB.'
        form = response.context.get('form')
        self.assertIn(message, form.errors['image'])

    def test_avatar_not_accepted_in_production(self):
        login(self, self.user, 'password')
        with self.settings(DEBUG=False):
            response = self.client.post(self.user_edit_url, self.valid_data)
        self.assertEqual(response.status_code, 302)
        
        self.assertEqual(Attachment.objects.count(), 0)

        self.user.refresh_from_db()
        self.assertEqual(self.user.avatar_url, None)
        self.assertEqual(self.user.gender, self.valid_data['gender'])
        self.assertEqual(self.user.signature, self.valid_data['signature'])
        self.assertEqual(self.user.location, self.valid_data['location'])
        self.assertEqual(self.user.website, self.valid_data['website'])

    def test_valid_data_acceptance(self):
        login(self, self.user, 'password')
        with self.settings(DEBUG=True):
            response = self.client.post(self.user_edit_url, self.valid_data)
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.avatar_url)
        self.assertEqual(self.user.gender, self.valid_data['gender'])
        self.assertEqual(self.user.signature, self.valid_data['signature'])
        self.assertEqual(self.user.location, self.valid_data['location'])
        self.assertEqual(self.user.website, self.valid_data['website'])

    def test_duplicate_images(self):
        login(self, self.user, 'password')
        with self.settings(DEBUG=True):
            response = self.client.post(self.user_edit_url, self.valid_data)
        self.assertEqual(response.status_code, 302)

        second_user = self.make_user('testuser2')
        client = Client()
        client.login(username=second_user.username, password='password')
        second_user_edit_url = reverse(
            'accounts:user_edit', kwargs={'username': second_user.username}
        )
        self.valid_data.update({'image': self.test_avatar_copy})
        data = self.valid_data
        with self.settings(DEBUG=True):
            second_response = client.post(second_user_edit_url, data)
        self.assertEqual(second_response.status_code, 302)

        self.user.refresh_from_db()
        second_user.refresh_from_db()
        self.assertIsNotNone(second_user.avatar_url)
        self.assertEqual(self.user.avatar_url, second_user.avatar_url)


class UserCommentListTest(TestCase):
    def test_list(self):
        user = self.make_user('testuser1')
        url = reverse(
            'accounts:user_comments', kwargs={'username': user.username}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['userprofile'], user)
        self.assertEqual(response.context['current_profile_page'], 'replies')
        self.assertIsInstance(response.context['comments'], Page)


class UserThreadListTest(TestCase):
    def test_auth_filter_str_for_guest(self):
        user = self.make_user('testuser1')
        for filter_str in ['new', 'following']:
            url = reverse(
                'accounts:thread_%s' % filter_str,
                kwargs={'username': user.username, 'filter_str': filter_str}
            )
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)

    def test_list(self):
        user = self.make_user('testuser1')
        login(self, user, 'password')
        for filter_str in ['new', 'following', 'me']:
            name_suffix = filter_str
            if filter_str == 'me':
                name_suffix = 'user'
            url = reverse(
                'accounts:thread_%s' % name_suffix,
                kwargs={'username': user.username, 'filter_str': filter_str}
            )
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['userprofile'], user)
            self.assertEqual(
                response.context['current_profile_page'], filter_str)
            self.assertEqual(response.context['base_url'][0], url)
            self.assertIsInstance(response.context['threads'], Page)


class SignupTest(TestCase):
    def setUp(self):
        self.url = reverse('accounts:signup')
        self.valid_data = {
            'username': 'testuser1',
            'email': 'testuser1@example.com',
            'password1': 'random-password',
            'password2': 'random-password'
        }

    def test_render(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_valid_data_acceptance(self):
        with self.settings(CONFIRM_EMAIL=True):
            response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='testuser1').exists())
    
    def test_without_email_confirmation(self):
        with self.settings(CONFIRM_EMAIL=False):
            self.valid_data.pop('email')
            response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='testuser1')
        self.assertEqual(user.email, '')

    def test_guest_signup(self):
        response = self.client.post(reverse('accounts:guest_signup'))
        self.assertEqual(response.status_code, 302)
        user_qs = User.objects.filter(username__icontains='guest')
        self.assertTrue(user_qs.exists())
        self.assertEqual(user_qs.count(), 1)

    def test_email_sent(self):
        with self.settings(CONFIRM_EMAIL=True):
            response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Activate Your ClassicForum Account')


class ActivateTest(TestCase):
    def test_render(self):
        """User """
        user = self.make_user('testuser1')
        user.is_active = False
        user.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk)).decode()
        token = account_activation_token.make_token(user)
        url = reverse(
            'accounts:activate', kwargs={'uidb64': uid, 'token': token}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.email_confirmed)
        self.assertTrue(user.is_active)


class FollowUserTest(TestCase):
    def setUp(self):
        self.user1 = self.make_user('testuser1')
        self.user2 = self.make_user('testuser2')
        self.url1 = reverse(
            'accounts:user_follow',
            kwargs={'username': self.user1.username}
        )
        self.url2 = reverse(
            'accounts:user_follow',
            kwargs={'username': self.user2.username}
        )

    def test_anonymous_user_redirect(self):
        """An anonymous user should be redirected to the login page"""
        redirect_url = '%s?next=%s' % (
            reverse('accounts:login'), self.url1)

        post_response = self.client.post(self.url1)
        self.assertRedirects(post_response, redirect_url)

        # data = {'message': 'hello word'}
        # post_response = self.client.post(self.url1, data)
        # self.assertRedirects(post_response, redirect_url)

    def test_follow(self):
        login(self, self.user2.username, 'password')
        response = self.client.post(self.url1)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.user2, self.user1.followers.all())
        self.assertIn(self.user1, self.user2.following.all())
        self.assertNotIn(self.user1, self.user2.followers.all())

    def test_unfollow(self):
        login(self, self.user2.username, 'password')
        response = self.client.post(self.url1)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.user2, self.user1.followers.all())

        response = self.client.post(self.url1)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(self.user2, self.user1.followers.all())

    def test_follow_each_other(self):
        login(self, self.user2.username, 'password')
        response = self.client.post(self.url1)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.user2, self.user1.followers.all())
        self.client.logout()

        login(self, self.user1.username, 'password')
        response = self.client.post(self.url2)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.user1, self.user2.followers.all())

    def test_cannot_follow_self(self):
        login(self, self.user2.username, 'password')
        response = self.client.post(self.url2)
        self.assertEqual(response.status_code, 404)


class UserFollowingTest(TestCase):
    def test_render(self):
        user = self.make_user('testuser1')
        url = reverse(
            'accounts:user_following',
            kwargs={'username': user.username}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['userprofile'], user)
        self.assertEqual(
            response.context['current_profile_page'], 'user_following'
        )
        self.assertIn('user_following', response.context)


class UserFollowersTest(TestCase):
    def test_render(self):
        user = self.make_user('testuser1')
        url = reverse(
            'accounts:user_followers',
            kwargs={'username': user.username}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['userprofile'], user)
        self.assertEqual(
            response.context['current_profile_page'], 'user_followers'
        )
        self.assertIn('user_followers', response.context)


class UserMentionTest(TestCase):
    def test_render(self):
        user1 = self.make_user('testuser1')
        user2 = self.make_user('testuser2')
        user3 = self.make_user('odd_testuser3')
        start_with = 'te'
        url = reverse('accounts:user_mention')
        response = self.client.get(url + '?username=' + start_with)
        expected_list = [
            {
                'username': 'testuser1', 'profile_url': '/accounts/testuser1/',
                'avatar_url': '/static/img/avatar.svg'
            },
            {
                'username': 'testuser2', 'profile_url': '/accounts/testuser2/',
                'avatar_url': '/static/img/avatar.svg'
            }
        ]
        self.assertListEqual(response.json()['user_list'], expected_list)


class UserMentionListTest(TestCase):
    def test_render(self):
        user1 = self.make_user('testuser1')
        user2 = self.make_user('testuser2')
        user3 = self.make_user('testuser3')
        username_list = '[{"username": "testuser1"}, {"username": "testuser2"}, {"username": "testuser3"}]'
        url = reverse('accounts:user_mention_list')
        response = self.client.get(url + '?username_list=' + username_list)
        self.assertEqual(response.status_code, 200)
        expected_list = [
            {
                'username': 'testuser1',
                'profile_url': '/accounts/testuser1/',
                'avatar_url': '/static/img/avatar.svg'
            },
            {
                'username': 'testuser2',
                'profile_url': '/accounts/testuser2/',
                'avatar_url': '/static/img/avatar.svg'
            },
            {
                'username': 'testuser3',
                'profile_url': '/accounts/testuser3/',
                'avatar_url': '/static/img/avatar.svg'
            }
        ]
        self.assertListEqual(response.json()['user_list'], expected_list)
