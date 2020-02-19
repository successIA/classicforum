import os
import shutil

from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.exceptions import FieldError
from django.utils import timezone
from django.urls import reverse

from test_plus import TestCase

from forum.notifications.models import Notification
from forum.threads.models import ThreadFollowership

from forum.comments.models import Comment, CommentRevision
from forum.comments.tests.utils import make_comment
from forum.threads.tests.utils import make_only_thread
from forum.categories.tests.utils import make_category


class NotificationModelTest(TestCase):
    def setUp(self):
        self.sender = self.make_user('ahmed')
        self.receiver = self.make_user('zainab')
        self.category = make_category()
        self.thread = make_only_thread(self.sender, self.category)
        self.comment = make_comment(self.sender, self.thread)

    def test_save_using_thread_and_comment(self):
        notification = Notification(
            sender=self.sender,
            receiver=self.receiver,
            thread=self.thread,
            comment=self.comment,
            notif_type=Notification.THREAD_CREATED
        )
        msg = 'Notification cannot have both comment field and thread field set.'
        with self.assertRaisesMessage(FieldError, msg):
            notification.save()

    def test_save_using_thread_and_invalid_notif_type(self):
        notification = Notification(
            sender=self.sender,
            receiver=self.receiver,
            thread=self.thread,
            notif_type=Notification.COMMENT_LIKED
        )
        msg = 'Invalid notification type for field thread'
        with self.assertRaisesMessage(FieldError, msg):
            notification.save()

    def test_save_using_comment_and_invalid_notif_type(self):
        notification = Notification(
            sender=self.sender,
            receiver=self.receiver,
            comment=self.comment,
            notif_type=Notification.THREAD_CREATED
        )
        msg = 'Invalid notification type for field comment'
        with self.assertRaisesMessage(FieldError, msg):
            notification.save()

    def test_save_using_invalid_notif_type(self):
        notification = Notification(
            sender=self.sender,
            receiver=self.receiver,
            comment=self.comment,
            notif_type='invalid notif type'
        )
        msg = 'Invalid notification type'
        with self.assertRaisesMessage(FieldError, msg):
            notification.save()

    def test_get_description_for_thread_create(self):
        notification = Notification(
            sender=self.sender,
            receiver=self.receiver,
            thread=self.thread,
            notif_type=Notification.THREAD_CREATED,
            created=timezone.now()
        )
        response_string = notification.get_description()
        self.assertIn('started a new thread', response_string)

    def test_get_description_for_thread_create(self):
        notification = Notification(
            sender=self.sender,
            receiver=self.receiver,
            thread=self.thread,
            notif_type=Notification.THREAD_CREATED,
            created=timezone.now()
        )
        response_string = notification.get_description()
        self.assertIn('started a new thread', response_string)

    def test_get_description_for_thread_update(self):
        notification = Notification(
            sender=self.sender,
            receiver=self.receiver,
            thread=self.thread,
            notif_type=Notification.THREAD_UPDATED,
            created=timezone.now()
        )
        response_string = notification.get_description()
        self.assertIn('updated a thread you are following', response_string)

    def test_get_description_for_comment_like(self):
        notification = Notification(
            sender=self.sender,
            receiver=self.receiver,
            comment=self.comment,
            notif_type=Notification.COMMENT_LIKED,
            created=timezone.now()
        )
        response_string = notification.get_description()
        self.assertIn('liked your comment', response_string)

    def test_get_description_for_comment_replied(self):
        notification = Notification(
            sender=self.sender,
            receiver=self.receiver,
            comment=self.comment,
            notif_type=Notification.COMMENT_REPLIED,
            created=timezone.now()
        )
        response_string = notification.get_description()
        self.assertIn('replied to your comment', response_string)

    def test_get_description_for_user_mentioned(self):
        notification = Notification(
            sender=self.sender,
            receiver=self.receiver,
            comment=self.comment,
            notif_type=Notification.USER_MENTIONED,
            created=timezone.now()
        )
        response_string = notification.get_description()
        self.assertIn('mentioned you in a comment', response_string)

    def test_get_precise_url(self):
        notification = Notification(
            sender=self.sender,
            receiver=self.receiver,
            comment=self.comment,
            notif_type=Notification.USER_MENTIONED,
            created=timezone.now()
        )
        expected_url = '%s?page=%s' % (
            reverse(
                'accounts:user_notifs',
                kwargs={'username': self.receiver.username}
            ),
            3
        )
        self.assertEqual(notification.get_precise_url(9), expected_url)


class NotificationQuerySetManagerTest(TestCase):
    def setUp(self):
        self.sender = self.make_user('ahmed')
        self.receiver = self.make_user('zainab')
        self.receiver2 = self.make_user('bola')
        self.receiver_list = [self.receiver, self.receiver2]
        self.category = make_category()
        self.thread = make_only_thread(self.sender, self.category)
        self.comment = make_comment(self.sender, self.thread)

    def test_notify_receiver_for_reply(self):
        reply = make_comment(self.sender, self.thread)
        reply.parent = self.comment
        reply.save()
        Notification.objects.create(
            sender=reply.user,
            receiver=reply.parent.user,
            comment=reply,
            notif_type=Notification.COMMENT_REPLIED
        )
        self.assertEqual(Notification.objects.count(), 1)

    def test_notify_mentioned_users(self):
        notif = Notification(
            sender=self.comment.user,
            comment=self.comment,
            notif_type=Notification.USER_MENTIONED
        )
        Notification.objects.notify_users(notif, self.receiver_list)
        notifs = Notification.objects.all()
        self.assertEqual(notifs[0].receiver, self.receiver)
        self.assertEqual(notifs[1].receiver, self.receiver2)
        notif_qs = Notification.objects.filter(
            notif_type=Notification.USER_MENTIONED
        )
        self.assertTrue(notif_qs.count(), 2)

    def test_notify_user_followers_for_thread_creation(self):
        user = self.make_user('user')
        ThreadFollowership.objects.create(user=user, thread=self.thread)
        for receiver in self.receiver_list:
            self.sender.followers.add(receiver)

        notif = Notification(
            sender=self.thread.user, 
            thread=self.thread, 
            notif_type=Notification.THREAD_CREATED
        )
        Notification.objects.notify_users(
           notif, self.thread.user.followers.all()
        )

        notifs = Notification.objects.all()
        self.assertEqual(notifs[0].receiver, self.receiver)
        self.assertEqual(notifs[1].receiver, self.receiver2)
        self.assertNotIn(user, notifs)
        self.assertNotIn(self.sender, notifs)
        notif_qs = Notification.objects.filter(
            notif_type=Notification.THREAD_CREATED
        )
        self.assertTrue(notif_qs.count(), 2)

    def test_notify_thread_followers_for_modification(self):
        user = self.make_user('user')
        self.sender.followers.add(user)
        for receiver in self.receiver_list:
            ThreadFollowership.objects.create(
                user=receiver, thread=self.thread
            )
        notif = Notification(
            sender=self.thread.user, 
            thread=self.thread, 
            notif_type=Notification.THREAD_UPDATED
        )
        Notification.objects.notify_users(
           notif, self.thread.followers.all()
        )

        notifs = Notification.objects.all()
        self.assertEqual(notifs[0].receiver, self.receiver)
        self.assertEqual(notifs[1].receiver, self.receiver2)
        self.assertNotIn(user, notifs)
        self.assertNotIn(self.sender, notifs)
        notif_qs = Notification.objects.filter(
            notif_type=Notification.THREAD_UPDATED
        )
        self.assertTrue(notif_qs.count(), 2)

    def test_mark_as_read(self):
        notif1 = Notification.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            comment=self.comment,
            notif_type=Notification.COMMENT_LIKED
        )
        notif2 = Notification.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            thread=self.thread,
            notif_type=Notification.THREAD_UPDATED
        )
        notif3 = Notification.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            thread=self.thread,
            notif_type=Notification.THREAD_CREATED
        )
        Notification.objects.mark_as_read(
            self.receiver, [notif1.pk, notif2.pk]
        )
        for notif in Notification.objects.exclude(pk=notif3.pk):
            self.assertFalse(notif.unread)
        notif3.refresh_from_db()
        self.assertTrue(notif3.unread)

    def test_get_receiver_url_and_count(self):
        notif1 = Notification.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            comment=self.comment,
            notif_type=Notification.COMMENT_LIKED,
            unread=False
        )
        notif2 = Notification.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            thread=self.thread,
            notif_type=Notification.THREAD_UPDATED
        )
        notif3 = Notification.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            thread=self.thread,
            notif_type=Notification.THREAD_CREATED
        )
        url, count = Notification.objects.get_receiver_url_and_count(
            self.receiver
        )
        self.assertEqual(url, notif2.get_precise_url(1))
        self.assertEqual(count, 2)
