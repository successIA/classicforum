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
from forum.comments.models import Comment
from forum.notifications.models import Notification
from forum import testutils

import datetime



class NotificationTests(TestCase):
    def setUp(self):
        # testutils.sign_up_a_new_user('janet')
        # testutils.sign_up_a_new_user('bola')
        # testutils.sign_up_a_new_user('abdullah')
        self.user1 = User.objects.create_user(username='john', email='john@example.com', password='pass1234')
        self.user2 = User.objects.create_user(username='janet', email='janet@example.com', password='pass1234')
        self.user3 = User.objects.create_user(username='bola', email='bola@example.com', password='pass1234')
        self.user4 = User.objects.create_user(username='abdullahi', email='abdullahi@example.com', password='pass1234')

        self.userprofile1 = UserProfile.objects.create(user=self.user1)
        self.userprofile2 = UserProfile.objects.create(user=self.user2)
        self.userprofile3 = UserProfile.objects.create(user=self.user3)
        self.userprofile4 = UserProfile.objects.create(user=self.user4)

        # self.response = self.client.get(self.userprofile.get_absolute_url())
        self.category = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='django')
        self.category2 = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='django')
        self.thread = Thread.objects.create(title='Galaxy S5 Discussion Thread', body='Lorem ipsum dalor', category=self.category, user=self.user1)
        self.thread2 = Thread.objects.create(title='Galaxy S5 Discussion Thread', body='Lorem ipsum dalor', category=self.category, user=self.user2)

        # self.thread_follow_url = self.thread.get_thread_follow_url()


    def test_only_thread_followers_get_notification(self):
        self.userprofile2.thread_following.add(self.thread)
        self.userprofile3.thread_following.add(self.thread)
        comment1 = Comment.objects.create(message='Hello World!', thread=self.thread, user=self.user1)
        notif_user2 = Notification.objects.filter(receiver=self.userprofile2.user, comment=comment1).first()
        self.assertEquals(comment1.message, notif_user2.comment.message)

        notif_user3 = Notification.objects.filter(receiver=self.userprofile2.user, comment=comment1).first()
        self.assertEquals(comment1.message, notif_user3.comment.message)

        comment2 = Comment.objects.create(message='Hello World!', thread=self.thread, user=self.user2)
        notif_user1 = Notification.objects.filter(receiver=self.userprofile1.user, comment=comment2).first()
        self.assertEquals(comment2.message, notif_user1.comment.message)

        notif_user3 = Notification.objects.filter(receiver=self.userprofile3.user, comment=comment2).first()
        self.assertEquals(comment2.message, notif_user3.comment.message)

        notif_user4 = Notification.objects.filter(receiver=self.userprofile4.user, comment=comment1).first()
        self.assertEquals(notif_user4, None)

        self.userprofile4.thread_following.add(self.thread2)
        notif_user4 = Notification.objects.filter(receiver=self.userprofile4.user, comment=comment1).first()
        self.assertEquals(notif_user4, None)

        comment3 = Comment.objects.create(message='Hello World!', thread=self.thread2, user=self.user3)
        notif_user4 = Notification.objects.filter(receiver=self.userprofile4.user, comment=comment3).first()
        self.assertEquals(comment3.message, notif_user4.comment.message)



        # user2.userprofile.toggle_thread_following(self.thread)
        # user3.userprofile.toggle_thread_following(self.thread)
        # user4.userprofile.toggle_thread_following(self.thread)

        # self.client.logout()
        # testutils.sign_up_a_new_user(self, 'john')
        # self.message = 'Hello World'
        # self.thread_slug = self.thread.slug
        # self.response = self.client.post(self.thread.get_comment_url(),
        #                                  {'message': self.message, 'thread_slug': self.thread_slug})
        # Notification.objects.filter(thread=self.thread, receiver=user2.userprofile, comment=)

   