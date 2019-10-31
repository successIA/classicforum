from django.test import TestCase
from django.contrib.auth.models import User

from forum.categories.models import Category
from forum.threads.models import Thread
from forum.comments.models import Comment

from forum.templatetags import forum_template_tags

from forum import testutils


class ThreadCategoryInit(TestCase):
    def setUp(self):
        testutils.sign_up_a_new_user(self, 'john')
        self.user = User.objects.get(id=1)

        self.category = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='django')
        self.thread = Thread.objects.create(title='Galaxy S5 Discussion Thread', body='Lorem ipsum dalor', category=self.category, user=self.user)


class ThreadIndicatorTag(ThreadCategoryInit):
    def test_thread_indicator_filter(self):
        abs_url = forum_template_tags.old_thread_indicator(self.thread.get_absolute_url() + '#comment1')
        expecting = self.thread.get_absolute_url
        self.assertEquals(abs_url, expecting)
