from datetime import timedelta
import os
import shutil

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from django.test import RequestFactory

from test_plus import TestCase
from faker import Faker

from forum.attachments.models import Attachment
from forum.accounts.models import User

fake = Faker()

TEST_AVATARS_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'testavatars'
)
TEST_AVATAR_1 = os.path.join(TEST_AVATARS_DIR, 'aprf1.jpg')

AVATAR_UPLOAD_DIR = os.path.join(settings.TEST_MEDIA_ROOT, 'avatars')


@override_settings(MEDIA_ROOT=settings.TEST_MEDIA_ROOT)
class UserModelTest(TestCase):
    def setUp(self):
        self.user = self.make_user('john')
        self.test_avatar = SimpleUploadedFile(
            name='aprf1.jpg',
            content=open(TEST_AVATAR_1, 'rb').read(),
            content_type='image/jpeg'
        )

    def tearDown(self):
        self.test_avatar.close()
        try:
            if os.path.isdir(settings.TEST_MEDIA_ROOT):
                shutil.rmtree(settings.TEST_MEDIA_ROOT)
        except Exception as e:
            print(e)

    def test_str_(self):
        self.assertEquals(self.user.__str__(), self.user.username)

    def test_is_online(self):
        self.user.last_seen = timezone.now()
        self.assertTrue(self.user.is_online())

    def test_is_online_with_below_10_minutes(self):
        self.user.last_seen = timezone.now() - timedelta(seconds=10*60)
        self.assertFalse(self.user.is_online())

    def test_is_owner(self):
        user = User.objects.get(username='john')
        self.assertTrue(self.user.is_owner(user))

    def test_not_owner(self):
        second_user = self.make_user('second_user')
        self.assertFalse(self.user.is_owner(second_user))

    def test_is_required_filter_with_owner(self):
        user = User.objects.get(username='john')
        for filter_str in ['me', 'following', 'new']:
            self.assertTrue(
                self.user.is_required_filter_owner(user, filter_str)
            )

    def test_is_required_filter_with_not_owner(self):
        second_user = self.make_user('second_user')
        for filter_str in ['me', 'following', 'new']:
            self.assertFalse(
                self.user.is_required_filter_owner(second_user, filter_str)
            )

    def test_get_avatar_url_with_avatar(self):
        url = Attachment.objects.create_avatar(self.test_avatar, self.user)
        self.user.avatar_url = url
        self.user.save()
        self.assertEquals(self.user.get_avatar_url(), url)

    def test_get_avatar_url_without_avatar(self):
        self.assertIsNone(self.user.get_avatar_url())

    def test_update_notification_info(self):
        request = RequestFactory()
        request.user = self.user
        url = '/notification_url_example/'
        count = 99
        self.user.update_notification_info(request, url, count)
        self.assertEquals(request.user.notif_url, url)
        self.assertEquals(request.user.notif_count, count)

    def test_toggle_followers_with_new_follower(self):
        second_user = self.make_user('second_user')
        self.user.toggle_followers(second_user)
        self.assertIn(second_user, self.user.followers.all())
        self.assertNotIn(self.user, second_user.followers.all())

    def test_toggle_followers_with_existing_follower(self):
        second_user = self.make_user('second_user')
        self.user.followers.add(second_user)
        self.user.toggle_followers(second_user)
        self.assertNotIn(second_user, self.user.followers.all())

    def test_get_absolute_url(self):
        url = '/accounts/%s/' % self.user.username
        self.assertEquals(self.user.get_absolute_url(), url)

    def test_get_user_follow_url(self):
        url = '/accounts/%s/follow/' % self.user.username
        self.assertEquals(self.user.get_user_follow_url(), url)

    def test_get_userprofile_update_url(self):
        url = '/accounts/%s/info/' % self.user.username
        self.assertEquals(self.user.get_userprofile_update_url(), url)

    def test_get_login_url(self):
        url = '/accounts/auth/login/'
        self.assertEquals(self.user.get_login_url(), url)
