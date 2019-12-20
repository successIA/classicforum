from datetime import timedelta
import os
import shutil

from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from forum.accounts.tokens import account_activation_token
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings, Client
from django.urls import reverse
from django.utils import timezone
from django.test import RequestFactory
from django.core.paginator import Page
from django.core import mail

from test_plus import TestCase
from faker import Faker

from forum.accounts.models import User
from forum.accounts.tests.utils import login
from forum.accounts.forms import UserProfileForm
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
        user = self.make_user('john')
        url = reverse(
            'accounts:user_stats', kwargs={'username': user.username}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['userprofile'], user)
        self.assertEqual(response.context['dropdown_active_text2'], 'stats')
        self.assertIn('comment_count', response.context)
        self.assertIn('followers', response.context)
        self.assertIn('following', response.context)
        self.assertIn('last_posted', response.context)
        self.assertIn('active_category', response.context)
        self.assertIn('total_upvotes', response.context)
        self.assertIn('total_upvoted', response.context)
        self.assertIsInstance(
            response.context['recent_comments'], CommentQuerySet
        )
        self.assertIsInstance(
            response.context['recent_threads'], ThreadQuerySet
        )


class UserNotificationList(TestCase):
    def setUp(self):
        self.user = self.make_user('john')
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
        second_user = self.make_user('second_user')
        login(self, second_user, 'password')
        response = self.client.get(self.notif_url)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_user_with_permission(self):
        login(self, self.user, 'password')
        response = self.client.get(self.notif_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['userprofile'], self.user)
        self.assertEqual(
            response.context['dropdown_active_text2'], 'user_notifs')
        self.assertIsInstance(response.context['notifications'], Page)


@override_settings(MEDIA_ROOT=settings.TEST_MEDIA_ROOT)
class UserProfileEditTest(TestCase):
    def setUp(self):
        self.user = self.make_user('john')
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
        second_user = self.make_user('second_user')
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
            response.context['dropdown_active_text2'], 'settings')
        self.assertIsInstance(response.context['form'], UserProfileForm)

    def test_large_image(self):
        login(self, self.user, 'password')
        self.valid_data.update({'image': self.test_avatar_large})
        data = self.valid_data
        response = self.client.post(self.user_edit_url, data)
        self.assertEqual(response.status_code, 200)
        message = 'File too large. Size should not exceed 500 KB.'
        form = response.context.get('form')
        self.assertIn(message, form.errors['image'])

    def test_valid_data_acceptance(self):
        login(self, self.user, 'password')
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
        response = self.client.post(self.user_edit_url, self.valid_data)
        self.assertEqual(response.status_code, 302)

        second_user = self.make_user('second_user')
        client = Client()
        client.login(username=second_user.username, password='password')
        second_user_edit_url = reverse(
            'accounts:user_edit', kwargs={'username': second_user.username}
        )
        self.valid_data.update({'image': self.test_avatar_copy})
        data = self.valid_data
        second_response = client.post(second_user_edit_url, data)
        self.assertEqual(second_response.status_code, 302)

        self.user.refresh_from_db()
        second_user.refresh_from_db()
        self.assertIsNotNone(second_user.avatar_url)
        self.assertEqual(self.user.avatar_url, second_user.avatar_url)


class UserCommentListTest(TestCase):
    def test_list(self):
        user = self.make_user('john')
        url = reverse(
            'accounts:user_comments', kwargs={'username': user.username}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['userprofile'], user)
        self.assertEqual(response.context['dropdown_active_text2'], 'replies')
        self.assertIsInstance(response.context['comments'], Page)


class UserThreadListTest(TestCase):
    def test_list(self):
        user = self.make_user('john')
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
                response.context['dropdown_active_text2'], filter_str)
            self.assertEqual(response.context['threads_url'] + '/', url)
            self.assertIsInstance(response.context['threads'], Page)


class SignupTest(TestCase):
    def setUp(self):
        self.url = reverse('accounts:signup')
        self.valid_data = {
            'username': 'john',
            'email': 'john@example.com',
            'email2': 'john@example.com',
            'password1': 'random-password',
            'password2': 'random-password'
        }

    def test_render(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_valid_data_acceptance(self):
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='john').exists())

    def test_email_sent(self):
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Activate Your Forum Account')


class ActivateTest(TestCase):
    def test_render(self):
        """User """
        user = self.make_user('john')
        user.is_active = False
        user.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        url = reverse(
            'accounts:activate', kwargs={'uidb64': uid, 'token': token}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.email_confirmed)
        self.assertTrue(user.is_active)


class FollowUserTest(TestCase):
    def setUp(self):
        self.user1 = self.make_user('john')
        self.user2 = self.make_user('ahmed')
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

        get_response = self.client.get(self.url1)
        self.assertRedirects(get_response, redirect_url)

        data = {'message': 'hello word'}
        post_response = self.client.post(self.url1, data)
        self.assertRedirects(post_response, redirect_url)

    def test_follow(self):
        login(self, self.user2.username, 'password')
        response = self.client.get(self.url1)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.user2, self.user1.followers.all())
        self.assertIn(self.user1, self.user2.following.all())
        self.assertNotIn(self.user1, self.user2.followers.all())

    def test_unfollow(self):
        login(self, self.user2.username, 'password')
        response = self.client.get(self.url1)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.user2, self.user1.followers.all())

        response = self.client.get(self.url1)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(self.user2, self.user1.followers.all())

    def test_follow_each_other(self):
        login(self, self.user2.username, 'password')
        response = self.client.get(self.url1)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.user2, self.user1.followers.all())
        self.client.logout()

        login(self, self.user1.username, 'password')
        response = self.client.get(self.url2)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.user1, self.user2.followers.all())

    def test_cannot_follow_self(self):
        login(self, self.user2.username, 'password')
        response = self.client.get(self.url2)
        self.assertEqual(response.status_code, 404)


class UserFollowingTest(TestCase):
    def test_render(self):
        user = self.make_user('john')
        url = reverse(
            'accounts:user_following',
            kwargs={'username': user.username}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['userprofile'], user)
        self.assertEqual(
            response.context['dropdown_active_text2'], 'user_following'
        )
        self.assertIn('user_following', response.context)


class UserFollowersTest(TestCase):
    def test_render(self):
        user = self.make_user('john')
        url = reverse(
            'accounts:user_followers',
            kwargs={'username': user.username}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['userprofile'], user)
        self.assertEqual(
            response.context['dropdown_active_text2'], 'user_followers'
        )
        self.assertIn('user_followers', response.context)


class UserMentionTest(TestCase):
    def test_render(self):
        user1 = self.make_user('john')
        user2 = self.make_user('joshua')
        user3 = self.make_user('drogba')
        start_with = 'jo'
        url = reverse('accounts:user_mention')
        response = self.client.get(url + '?username=' + start_with)
        expected_list = [
            {
                'username': 'john', 'profile_url': '/accounts/john/',
                'avatar_url': '/static/img/avatar.svg'
            },
            {
                'username': 'joshua', 'profile_url': '/accounts/joshua/',
                'avatar_url': '/static/img/avatar.svg'
            }
        ]
        self.assertListEqual(response.json()['user_list'], expected_list)


class UserMentionListTest(TestCase):
    def test_render(self):
        user1 = self.make_user('john')
        user2 = self.make_user('joshua')
        user3 = self.make_user('drogba')
        username_list = '[{"username": "john"}, {"username": "joshua"}, {"username": "drogba"}]'
        url = reverse('accounts:user_mention_list')
        response = self.client.get(url + '?username_list=' + username_list)
        self.assertEqual(response.status_code, 200)
        expected_list = [
            {
                'username': 'john',
                'profile_url': '/accounts/john/',
                'avatar_url': '/static/img/avatar.svg'
            },
            {
                'username': 'joshua',
                'profile_url': '/accounts/joshua/',
                'avatar_url': '/static/img/avatar.svg'
            },
            {
                'username': 'drogba',
                'profile_url': '/accounts/drogba/',
                'avatar_url': '/static/img/avatar.svg'
            }
        ]
        self.assertListEqual(response.json()['user_list'], expected_list)
