import urllib.parse

from django.core.paginator import Page
from django.urls import reverse
from django.utils import timezone

from faker import Faker
from test_plus import TestCase

from forum.categories.tests.utils import make_category
from forum.accounts.tests.utils import login
from forum.comments.forms import Comment, CommentForm
from forum.comments.utils import get_bbcode_message_quote
from forum.threads.forms import ThreadForm
from forum.threads.models import Thread
from forum.comments.tests.utils import make_comment
from forum.threads.tests.utils import make_threads, make_only_thread


fake = Faker()


class CommentViewsTest(TestCase):
    def setUp(self):
        self.user = self.make_user("john")
        self.category = make_category()
        self.thread = make_threads(
            count=1, user=self.user, category=self.category
        )


class CommentCreateViewTest(CommentViewsTest):
    def setUp(self):
        super().setUp()
        self.create_url = reverse(
            'comments:comment_create', kwargs={'thread_slug': self.thread.slug}
        )

    def test_anonymous_user_redirect(self):
        redirect_url = '%s?next=%s' % (
            reverse('accounts:login'), self.create_url
        )

        get_response = self.client.get(self.create_url)
        self.assertRedirects(get_response, redirect_url)

        data = {'message': 'hello word'}
        post_response = self.client.post(self.create_url, data)
        self.assertRedirects(post_response, redirect_url)

    def test_view_render_for_authenticated_user(self):
        """
        Logged in can access the comment create form directly
        """
        login(self, self.user, 'password')
        response = self.client.get(self.create_url)
        self.assertEquals(response.status_code, 200)
        self.assertIsInstance(response.context['form'], CommentForm)

    def test_view_submit_success_for_authenticated_user(self):
        current_count = Comment.objects.count()
        login(self, self.user, 'password')
        data = {'message': 'hello word'}
        response = self.client.post(self.create_url, data)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Comment.objects.count(), current_count + 1)

    def test_empty_data_cannot_be_posted(self):
        login(self, self.user, 'password')
        data = {}
        response = self.client.post(self.create_url, data)
        self.assertEquals(response.status_code, 200)
        form = response.context.get('form')
        self.assertTrue(form.errors)

    def test_invalid_data_cannot_be_posted(self):
        login(self, self.user, 'password')
        data = {'message': ''}
        response = self.client.post(self.create_url, data)
        self.assertEquals(response.status_code, 200)
        form = response.context.get('form')
        self.assertTrue(form.errors)


class CommentCreateViewWithMentionTest(CommentViewsTest):
    def setUp(self):
        super().setUp()
        self.create_url = reverse(
            'comments:comment_create', kwargs={'thread_slug': self.thread.slug}
        )
        self.mentioner = self.make_user('mentioner')
        login(self, self.mentioner, 'password')

    def test_post_with_invalid_mention(self):
        mentionee = self.make_user('mentionee')
        message = 'hello world @mentione'
        data = {'message': message}
        response = self.client.post(self.create_url, data)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Comment.objects.all().count(), 2)
        comment = Comment.objects.get(message=message)
        self.assertNotIn(mentionee, comment.mentioned_users.all())

    def test_post_with_valid_mention(self):
        mentionee = self.make_user('mentionee')
        message = 'hello world @mentionee'
        data = {'message': message}
        response = self.client.post(self.create_url, data)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Comment.objects.all().count(), 2)
        comment = Comment.objects.get(message=message)
        self.assertIn(mentionee, comment.mentioned_users.all())

    def test_post_with_repeated_mentions(self):
        first_mentionee = self.make_user('first_mentionee')
        second_mentionee = self.make_user('second_mentionee')
        mistake_mentionee = self.make_user('mistake_mentionee')
        invalid_mentionee = self.make_user('invalid_mentionee')
        message = """
        hello world @invalid_mentione ewe @second_mentionee dsd
        zksjks \n@mistake_mentioneednksdjkdj\rdfd   @first_mentionee...x
        @second_mentionee invalid_mentione
        """
        data = {'message': message}
        response = self.client.post(self.create_url, data)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Comment.objects.all().count(), 2)
        comment = Comment.objects.last()
        self.assertNotEquals(comment.mentioned_users.count(), 5)
        self.assertEquals(comment.mentioned_users.count(), 2)


class CommentCreateViewWithMarkedMessageTest(CommentViewsTest):
    def setUp(self):
        super().setUp()
        self.create_url = reverse(
            'comments:comment_create', kwargs={'thread_slug': self.thread.slug}
        )
        self.commenter = self.make_user('commenter')
        login(self, self.commenter, 'password')

    def test_message_with_newlines(self):
        message = """
        hello world
        """
        data = {'message': message}
        response = self.client.post(self.create_url, data)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Comment.objects.all().count(), 2)
        comment = Comment.objects.last()
        self.assertEquals(comment.marked_message, '<p>hello world</p>')


class CommentUpdateViewTest(CommentViewsTest):
    def setUp(self):
        super().setUp()
        self.comment = Comment.objects.create(
            message='hello world',
            thread=self.thread,
            user=self.user
        )
        self.update_url = reverse(
            'comments:comment_update',
            kwargs={'thread_slug': self.thread.slug, 'pk': self.comment.pk}
        )

    def test_anonymous_user_redirect(self):
        """An anonymous user should be redirected to the login page"""
        redirect_url = '%s?next=%s' % (
            reverse('accounts:login'), self.update_url)

        get_response = self.client.get(self.update_url)
        self.assertRedirects(get_response, redirect_url)

        data = {'message': 'hello word'}
        post_response = self.client.post(self.update_url, data)
        self.assertRedirects(post_response, redirect_url)

    def test_authenticated_user_with_no_permission(self):
        """
        Only comment owner can see the comment edit form and update comment
        """
        second_user = self.make_user('second_user')
        login(self, second_user, 'password')

        get_response = self.client.get(self.update_url)
        self.assertEquals(get_response.status_code, 403)

        data = {'message': 'hello word'}
        post_response = self.client.post(self.update_url, data)
        self.assertEquals(post_response.status_code, 403)

    def test_render_for_authenticated_user_with_permission(self):
        login(self, self.user, 'password')
        response = self.client.get(self.update_url)
        self.assertEquals(response.status_code, 200)
        self.assertIsInstance(response.context['form'], CommentForm)

    def test_empty_data_rejection(self):
        login(self, self.user, 'password')
        data = {}
        response = self.client.post(self.update_url, data)
        self.assertEquals(response.status_code, 200)
        form = response.context.get('form')
        self.assertTrue(form.errors)

    def test_invalid_data_rejection(self):
        login(self, self.user, 'password')
        data = {
            'category': 'Choose category',
            'title': '',
            'message': '',
        }
        response = self.client.post(self.update_url, data)
        self.assertEquals(response.status_code, 200)
        form = response.context.get('form')
        self.assertTrue(form.errors)

    def test_valid_data_acceptance(self):
        login(self, self.user, 'password')
        data = {'message': 'hello world changed'}
        response = self.client.post(self.update_url, data)
        self.assertEquals(response.status_code, 302)
        self.comment.refresh_from_db()
        self.assertEquals(self.comment.message, 'hello world changed')

    def test_starting_comment_change_rejection(self):
        """
        View does not display edit form or allow the update of starting comment
        """
        login(self, self.user, 'password')
        data = {'message': 'hello world change'}
        message = self.thread.starting_comment.message
        pk = self.thread.starting_comment.pk
        update_url = reverse(
            'comments:comment_update',
            kwargs={'thread_slug': self.thread.slug, 'pk': pk}
        )
        response = self.client.post(update_url, data)
        self.assertEquals(response.status_code, 404)


class CommentReplyViewTest(CommentViewsTest):
    def setUp(self):
        super().setUp()
        self.comment = Comment.objects.create(
            message='hello world',
            thread=self.thread,
            user=self.user
        )
        self.reply_url = reverse(
            'comments:comment_reply',
            kwargs={'thread_slug': self.thread.slug, 'pk': self.comment.pk}
        )
        self.bbcode_message = get_bbcode_message_quote(self.comment)

    def test_anonymous_user_redirect(self):
        """An anonymous user should be redirected to the login page"""
        redirect_url = '%s?next=%s' % (
            reverse('accounts:login'), self.reply_url)

        get_response = self.client.get(self.reply_url)
        self.assertRedirects(get_response, redirect_url)

        data = {'message': 'hello word\n' + self.bbcode_message}
        post_response = self.client.post(self.reply_url, data)
        self.assertRedirects(post_response, redirect_url)

    def test_render_for_authenticated_user(self):
        """Logged in users can see the reply form"""
        login(self, self.user, 'password')
        response = self.client.get(self.reply_url)
        self.assertEquals(response.status_code, 200)
        self.assertIsInstance(response.context['form'], CommentForm)
        self.assertEquals(
            self.bbcode_message, response.context['form'].initial['message']
        )

    def test_submit_success_for_authenticated_user(self):
        current_count = Comment.objects.count()
        second_user = self.make_user('second_user')
        login(self, second_user, 'password')
        reply_message = 'reply to hello world'
        message = self.bbcode_message + reply_message
        data = {'message': message}
        response = self.client.post(self.reply_url, data)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Comment.objects.count(), current_count + 1)
        self.assertEquals(Comment.objects.last().parent, self.comment)

    def test_empty_data_rejection(self):
        login(self, self.user, 'password')
        data = {}
        response = self.client.post(self.reply_url, data)
        self.assertEquals(response.status_code, 200)
        form = response.context.get('form')
        self.assertTrue(form.errors)

    def test_invalid_data_rejection(self):
        login(self, self.user, 'password')
        data = {'message': ''}
        response = self.client.post(self.reply_url, data)
        self.assertEquals(response.status_code, 200)
        form = response.context.get('form')
        self.assertTrue(form.errors)


class CommentUpvoteTest(CommentViewsTest):

    def setUp(self):
        super().setUp()
        self.comment = Comment.objects.create(
            message='hello world',
            category=self.thread.category,
            thread=self.thread,
            user=self.user
        )
        self.upvote_url = reverse(
            'comments:upvote',
            kwargs={'thread_slug': self.thread.slug, 'pk': self.comment.pk}
        )

    def test_anonymous_user_redirect(self):
        """An anonymous user should be redirected to the login page"""
        redirect_url = '%s?next=%s' % (
            reverse('accounts:login'), self.upvote_url)
        response = self.client.get(self.upvote_url)
        self.assertRedirects(response, redirect_url)

    def test_view_should_reject_owner(self):
        """An owner cannot upvote his/her comment"""
        login(self, self.user, 'password')
        response = self.client.get(self.upvote_url)
        self.assertEquals(response.status_code, 403)

    def test_new_voter(self):
        """A new voter is permitted to upvote a comment"""
        second_user = self.make_user('second_user')
        login(self, second_user, 'password')
        response = self.client.get(self.upvote_url)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.comment.upvoters.count(), 1)

    def test_existing_upvoter(self):
        """An existing voter is removed from upvoters count"""
        second_user = self.make_user('second_user')
        login(self, second_user, 'password')
        self.client.get(self.upvote_url)
        response = self.client.get(self.upvote_url)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.comment.upvoters.count(), 0)


class CommentDownvoteTest(CommentViewsTest):

    def setUp(self):
        super().setUp()
        self.comment = Comment.objects.create(
            message='hello world',
            thread=self.thread,
            user=self.user
        )
        self.downvote_url = reverse(
            'comments:downvote',
            kwargs={'thread_slug': self.thread.slug, 'pk': self.comment.pk}
        )

    def test_anonymous_user_redirect(self):
        """An anonymous user should be redirected to the login page"""
        redirect_url = '%s?next=%s' % (
            reverse('accounts:login'), self.downvote_url)
        response = self.client.get(self.downvote_url)
        self.assertRedirects(response, redirect_url)

    def test_view_should_reject_owner(self):
        """An owner cannot downvote his/her comment"""
        login(self, self.user, 'password')
        response = self.client.get(self.downvote_url)
        self.assertEquals(response.status_code, 403)

    def test_new_voter(self):
        """A new voter is permitted to downvote a comment"""
        second_user = self.make_user('second_user')
        login(self, second_user, 'password')
        response = self.client.get(self.downvote_url)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.comment.downvoters.count(), 1)

    def test_existing_downvoter(self):
        """An existing voter is removed from downvoters count"""
        second_user = self.make_user('second_user')
        login(self, second_user, 'password')
        self.client.get(self.downvote_url)
        response = self.client.get(self.downvote_url)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(self.comment.downvoters.count(), 0)
