# from django.contrib.auth.models import User
# from django.test import TestCase
# from django.urls import resolve, reverse
# from django.core.files.uploadedfile import SimpleUploadedFile

# from forum.accounts.forms import UserSignUpForm
# from forum.accounts.views import SignUpView
# from forum.accounts.models import UserProfile
# from forum.accounts.views import UserProfileView

# from forum.categories.models import Category
# from forum.threads.models import Thread
# from forum.comments.models import Comment
# from forum.notifications.models import Notification
# from forum import testutils

# import datetime



# class NotificationTests(TestCase):
#     def setUp(self):
#         testutils.sign_up_a_new_user('janet')
#         testutils.sign_up_a_new_user('bola')
#         testutils.sign_up_a_new_user('abdullah')
#         user1 = User.objects.get(username='john')
#         user2 = User.objects.get(username='janet')
#         user3 = User.objects.get(username='bola')
#         user4 = User.objects.get(username='abdullah')

#         # self.response = self.client.get(self.userprofile.get_absolute_url())
#         self.category = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='django')
#         self.thread = Thread.objects.create(title='Galaxy S5 Discussion Thread', body='Lorem ipsum dalor', category=self.category, user=self.user)
#         self.thread_follow_url = self.thread.get_thread_follow_url()


#     def test_all_users_notification(self):
#         user2.userprofile.toggle_thread_following(self.thread)
#         user3.userprofile.toggle_thread_following(self.thread)
#         user4.userprofile.toggle_thread_following(self.thread)

#         self.client.logout()
#         testutils.sign_up_a_new_user(self, 'john')
#         self.message = 'Hello World'
#         self.thread_slug = self.thread.slug
#         self.response = self.client.post(self.thread.get_comment_url(),
#                                          {'message': self.message, 'thread_slug': self.thread_slug})
#         Notification.objects.filter(thread=self.thread, receiver=user2.userprofile, comment=)

#     def test_userprofile_status_code(self):
#         self.assertEquals(self.response.status_code, 200)

#     def test_signup_url_resolves_signup_view(self):
#         view = resolve(self.userprofile.get_absolute_url())
#         self.assertEquals(view.func.view_class, UserProfileView)

#     def test_a_userprofile_may_follow_a_thread(self):
#         self.userprofile.toggle_thread_following(self.thread)
#         self.assertEquals(self.thread, self.userprofile.thread_following.first())

#     def test_a_userprofile_may_unfollow_a_thread(self):
#         self.userprofile.toggle_thread_following(self.thread)
#         self.userprofile.toggle_thread_following(self.thread)
#         self.assertEquals(None, self.userprofile.thread_following.first())

#     def test_userprofile_page_may_have_a_userprofile_context(self):
#         self.assertEquals(self.response.context.get('userprofile'), self.userprofile)

#     # def test_userprofile_page_may_have_a_followed_threads_context(self):
#         # '''
#         # todo: queryset equality issue
#         # '''
#     #     self.userprofile.followed_threads.add(self.thread)
#     #     response = self.client.get(self.userprofile.get_absolute_url())
#     #     self.assertEqual(response.context['followed_threads'], self.userprofile.followed_threads.all())

#     # def test_userprofile_page_may_not_have_a_followed_threads_context(self):
#         # '''
#         # todo: queryset equality issue
#         # '''
#     #     response = self.client.get(self.userprofile.get_absolute_url())
#     #
#     #     self.assertEqual(response.context['followed_threads'], self.userprofile.followed_threads.all())

#     def test_userprofile_page_may_have_a_username_context(self):
#         self.assertEqual(self.response.context['username'], self.userprofile.user.username)


# class UserFollowTest(TestCase):
#     def setUp(self):
#         url = reverse('signup')
#         data = {
#             'username': 'john',
#             'email': 'john@doe.com',
#             'password1': 'abcdef123456',
#             'password2': 'abcdef123456'
#         }
#         self.response = self.client.post(url, data)

#         self.user1 = User.objects.get(id=1)

#         self.user2 = User.objects.create_user(username='janet', email='janet@example.com', password='pass1234')
#         self.userprofile2 = UserProfile.objects.create(user=self.user2)
#         # self.client.login(username=self.user1.username, password=self.user1.password)

#     def test_user2_can_follow_user1(self):
#         self.user1.userprofile.user_followers.add(self.user2)
#         self.assertEquals(self.user1.userprofile.user_followers.first(), self.user2)

#     def test_user_follow_view(self):
#         response = self.client.get(self.userprofile2.get_user_follow_url())
#         print(self.user1.userprofile.user_followers.all())
#         self.assertEquals(self.user1.userprofile.user_followers.first(), self.user2)
#         self.assertEquals(response.status_code, 302)

#     def test_user_cannot_follow_self(self):
#         response = self.client.get(self.user1.userprofile.get_user_follow_url())
#         self.assertNotEquals(self.user1.userprofile.user_followers.first(), self.user1)
#         self.assertEquals(response.status_code, 404)

#     def test_visitor_redirect(self):
#         self.client.logout()
#         response = self.client.get(self.userprofile2.get_user_follow_url())
#         self.assertEquals(self.user1.userprofile.user_followers.first(), None)
#         self.assertEquals(response.status_code, 302)
