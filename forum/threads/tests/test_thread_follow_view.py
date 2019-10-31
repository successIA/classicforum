from django.core.urlresolvers import reverse, resolve
from django.test.client import RequestFactory
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from forum.categories.models import Category
from forum.threads.models import Thread, ThreadFollowership
from forum.comments.models import Comment
from forum.accounts.models import UserProfile

from forum import testutils


class FollowThreadInit(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='john', password='abcdef123456')
        userprofile = UserProfile.objects.create(user=user)

        user2 = User.objects.create_user(username='janet', password='abcdef123456')
        userprofile2 = UserProfile.objects.create(user=user2)

        # testutils.sign_up_a_new_user(self, 'john')
        self.client.login(username='janet', password='abcdef123456')
        self.user = User.objects.get(username='john')
        self.user2 = User.objects.get(username='janet')
        self.category = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='django')
        self.thread = Thread.objects.create(title='Galaxy S5 Discussion Thread', body='Lorem ipsum dalor', category=self.category, user=self.user)
        self.thread_follow_url = self.thread.get_thread_follow_url()
        # self.user_profile = UserProfile(user=self.user, thread=self.thread)


class FollowThreadTest(FollowThreadInit):
    def test_a_user_becomes_a_follower_of_a_thread_he_created(self):
        userprofile = self.user.userprofile
        t_fship = ThreadFollowership.objects.filter(
                    userprofile=userprofile, thread=self.thread
                  ).first()
        self.assertEquals(self.thread, t_fship.thread)

    def test_thread_follow_view_status_code(self):
        response = self.client.get(self.thread_follow_url)
        self.assertEquals(response.status_code, 302)

    def test_an_unauthenticated_user_cannot_follow_a_thread(self):
        self.client.logout()
        response = self.client.get(self.thread_follow_url)
        self.assertEquals(response.status_code, 302)
        login_url = '/accounts/login/?next=' + str(self.thread_follow_url)
        self.assertEquals(response.url, login_url)

    def test_user_can_unfollow_his_thread(self):
        self.client.login(username='john', password='abcdef123456')
        self.client.get(self.thread_follow_url)
        userprofile = self.user.userprofile
        t_fship = ThreadFollowership.objects.filter(
                    userprofile=userprofile, thread=self.thread
                  ).first()
        self.assertEquals(t_fship, None)

    def test_a_thread_can_be_followed_by_an_authenticated_user(self):
        self.client.get(self.thread_follow_url)
        userprofile = self.user2.userprofile
        t_fship = ThreadFollowership.objects.filter(
                    userprofile=userprofile, thread=self.thread
                  ).first()
        self.assertEquals(self.thread, t_fship.thread)

    def test_a_thread_can_be_unfollowed_by_an_authenticated_user(self):
        # user2 follows thread
        self.client.get(self.thread_follow_url)
        # user2 unfollows thread
        self.client.get(self.thread_follow_url)
        userprofile = self.user2.userprofile
        t_fship = ThreadFollowership.objects.filter(
                    userprofile=userprofile, thread=self.thread
                  ).first()
        self.assertEquals(t_fship, None)
    

class ThreadNewIndication(FollowThreadInit):
    def setUp(self):
        super().setUp()

        # logged in self.user follows a thread
        self.client.get(self.thread.get_thread_follow_url())
        user2 = User.objects.create_user(username='tope', email='john@doe.com', password='pass1234')

        # user2 create a new comment by interacting directly with the db without logging in
        comment = Comment.objects.create(message='python is awesome', thread=self.thread, user=user2)
        # at a later time
        comment.created = timezone.now() + timezone.timedelta(10000)
        comment.save()

        # self.user visits the category that displays the his followed thread
        self.response = self.client.get(self.category.get_absolute_url())

        '''
        Obtain the first item's absolute url in the thread queryset list
+        i.e '/topics/galaxy-s5-discussion-thread/#comment1'
        Note: the new thread comment url was adjusted after db query without updating it back
        do not use response.context.get('thread_qs').first().get_absolute_url()
        because it performs a fresh db query which will produce '/topics/galaxy-s5-discussion-thread/'
        '''
        self.thread_comment_link = list(self.response.context.get('thread_qs'))[0].get_absolute_url

    # def test_thread_show_new_to_its_users(self):
    #     expecting = '/topics/galaxy-s5-discussion-thread/#comment1'
    #     self.assertEquals(self.thread_comment_link, expecting)
    #     self.assertContains(self.response, self.thread_comment_link)

    # def test_thread_does_not_show_new_to_foreign_users(self):
    #     # logged in self.user unfollows a thread
    #     self.client.get(self.thread.get_thread_follow_url())
    #     # self.user visits the category that displays the his followed thread
    #     response = self.client.get(self.category.get_absolute_url())
    #     thread_comment_link = response.context.get('thread_qs').first().get_absolute_url()
    #     expecting = '/topics/galaxy-s5-discussion-thread/'
    #     self.assertEquals(thread_comment_link, expecting)
    #     self.assertContains(response, thread_comment_link)

    # def test_thread_does_not_show_new_to_visitors(self):
    #     # logout
    #     self.client.logout()

    #     response = self.client.get(self.category.get_absolute_url())

    #     thread_comment_link = response.context.get('thread_qs').first().get_absolute_url()
    #     expecting = '/topics/galaxy-s5-discussion-thread/'
    #     self.assertEquals(thread_comment_link, expecting)
    #     self.assertContains(response, thread_comment_link)
