from test_plus import TestCase

from forum.accounts.tests.utils import make_superuser
from forum.categories.tests.utils import make_category
from forum.comments.models import Comment
from forum.comments.tests.utils import make_comment
from forum.moderation.models import Moderator
from forum.threads.models import Thread
from forum.threads.tests.utils import make_only_thread


class ModeratorModelTest(TestCase):
    def setUp(self):
        self.user = self.make_user("testuser1")
        self.moderator = Moderator.objects.create(user=self.user)
    
        self.category = make_category()
        self.moderator.categories.add(self.category)

        self.user2 = self.make_user("testuser2")
        self.moderator2 = Moderator.objects.create(user=self.user2)    
        self.moderator2.categories.add(self.category)

        self.superuser = make_superuser("testuser3")
        self.supermoderator = Moderator.objects.create(
            user=self.superuser
        )
        self.supermoderator.categories.add(self.category)
        
        self.user3 = self.make_user("testuser4")
        self.moderator3 = Moderator.objects.create(user=self.user3)
        self.category2 = make_category(title="Business")
        self.moderator3.categories.add(self.category2)

        self.regular_user = self.make_user("testuser5")
    
    def test_save(self):
        """
        The is_moderator field of the moderator's user instance must
        be set after only creation.
        """
        self.assertTrue(self.moderator.user.is_moderator)
    
    def test_delete(self):
        """
        The is_moderator field of the moderator's user instance must
        be unset after deletion.
        """
        user = self.moderator.user
        self.moderator.delete()
        self.assertFalse(user.is_moderator)

    def test_get_hidden_posts(self):
        thread = make_only_thread(self.user, self.category)
        hidden_posts = self.moderator.get_hidden_posts(thread)
        self.assertQuerysetEqual(
            self.moderator.hidden_threads.all(), hidden_posts
        )

        comment = make_comment(self.user, thread)
        hidden_posts = self.moderator.get_hidden_posts(comment)
        self.assertQuerysetEqual(
            self.moderator.hidden_comments.all(), hidden_posts
        )

        msg = "post has to be an instance either Thread or Comment"
        with self.assertRaisesMessage(TypeError, msg):
            self.moderator.get_hidden_posts(self.category)
    
    def test_is_owner(self):
        self.assertFalse(self.moderator.is_owner(self.moderator2))
        self.assertTrue(self.moderator.is_owner(self.moderator))
    
    def test_is_supermoderator_to(self):        
        self.assertFalse(
            self.supermoderator.is_supermoderator_to(self.moderator3)
        )
        self.assertTrue(
            self.supermoderator.is_supermoderator_to(self.moderator)
        )
        self.assertTrue(
            self.supermoderator.is_supermoderator_to(self.moderator2)
        )
    
    def test_is_moderating_post(self):
        thread = make_only_thread(self.user, self.category)
        comment = make_comment(self.user, thread)
        
        self.assertFalse(self.moderator3.is_moderating_post(thread))
        self.assertFalse(self.moderator3.is_moderating_post(comment))

        self.assertTrue(self.moderator.is_moderating_post(thread))
        self.assertTrue(self.moderator.is_moderating_post(comment))
    
    def test_can_hide_post_without_post_moderator(self):
        """A moderator cannot hide a post he/she is not moderating"""
        thread = make_only_thread(self.regular_user, self.category)
        comment = make_comment(self.regular_user, thread)
        self.assertFalse(self.moderator3.can_hide_post(thread))
        self.assertFalse(self.moderator3.can_hide_post(comment))
        
    def test_can_hide_post_with_post_moderator(self):
        """Only a post moderator can hide the post he/she is moderating"""
        thread = make_only_thread(self.regular_user, self.category)
        comment = make_comment(self.regular_user, thread)
        self.assertTrue(self.moderator.can_hide_post(thread))
        self.assertTrue(self.moderator.can_hide_post(comment))

        thread = make_only_thread(self.superuser, self.category2)
        comment = make_comment(self.superuser, thread)
        self.assertTrue(self.moderator3.can_hide_post(thread))
        self.assertTrue(self.moderator3.can_hide_post(comment))

    def test_can_hide_post_without_moderator_owner(self):
        """A moderator cannot hide a post of another moderator"""
        thread = make_only_thread(self.user, self.category)
        comment = make_comment(self.user, thread)
        self.assertFalse(self.moderator2.can_hide_post(thread))
        self.assertFalse(self.moderator2.can_hide_post(comment))

    def test_can_hide_post_with_moderator_owner(self):
        """A moderator can hide his/her post"""
        thread = make_only_thread(self.user, self.category)
        comment = make_comment(self.user, thread)
        self.assertTrue(self.moderator.can_hide_post(thread))
        self.assertTrue(self.moderator.can_hide_post(comment))

    def test_can_hide_post_with_supermoderator_to_post(self):
        """A supermoderator can hide the post of another moderator"""
        thread = make_only_thread(self.user, self.category)
        comment = make_comment(self.user, thread)
        self.assertTrue(self.supermoderator.can_hide_post(thread))
        self.assertTrue(self.supermoderator.can_hide_post(comment))

    def test_can_hide_post_without_supermoderator_to_post(self):
        """A supermoderator cannot hide the post he/she is not moderating"""
        thread = make_only_thread(self.regular_user, self.category2)
        comment = make_comment(self.regular_user, thread)
        self.assertFalse(self.supermoderator.can_hide_post(thread))

    def test_can_hide_post_with_invisible_post(self):
        """An invisible post cannot be hidden"""
        thread = make_only_thread(self.user, self.category, visible=False)
        comment = make_comment(self.user, thread, visible=False)
        self.assertFalse(self.moderator.can_hide_post(thread))
        self.assertFalse(self.supermoderator.can_hide_post(thread))

        self.assertFalse(self.moderator.can_hide_post(comment))
        self.assertFalse(self.supermoderator.can_hide_post(comment))

    def test_can_hide_post_with_starting_comment(self):
        """A starting_comment cannot be hidden"""
        thread = make_only_thread(self.user, self.category, visible=False)
        comment = make_comment(self.user, thread, is_starting_comment=True)
        self.assertFalse(self.moderator.can_hide_post(comment))
        self.assertFalse(self.supermoderator.can_hide_post(comment))

    def test_can_unhide_post_with_visible_post(self):
        """A visible post cannot be unhidden"""
        thread = make_only_thread(self.superuser, self.category)
        comment = make_comment(self.superuser, thread)
        
        self.assertFalse(self.supermoderator.can_unhide_post(thread))
        self.assertFalse(self.supermoderator.can_unhide_post(comment))

        self.supermoderator.hidden_threads.add(thread)
        self.supermoderator.hidden_comments.add(comment)

        self.assertFalse(self.supermoderator.can_unhide_post(thread))
        self.assertFalse(self.supermoderator.can_unhide_post(comment))

    def test_can_unhide_post_without_post_moderator(self):
        """
        A post cannot unhidden by a moderator who is not moderating 
        the post.
        """
        thread = make_only_thread(
            self.regular_user, self.category2, visible=False
        )
        self.supermoderator.hidden_threads.add(thread)

        comment = make_comment(self.user, thread, visible=False)
        self.supermoderator.hidden_comments.add(comment)

        self.assertFalse(self.supermoderator.can_unhide_post(thread))
        self.assertFalse(self.supermoderator.can_unhide_post(comment))
    
    def test_can_unhide_post_without_owner(self):
        """
        A post cannot unhidden by a moderator who did not hide the post
        """
        thread = make_only_thread(
            self.regular_user, self.category, visible=False
        )
        self.moderator.hidden_threads.add(thread)

        comment = make_comment(self.user, thread, visible=False)
        self.moderator.hidden_comments.add(comment)

        self.assertFalse(self.moderator2.can_unhide_post(thread))
        self.assertFalse(self.moderator2.can_unhide_post(comment))

    def test_can_unhide_post_with_owner(self):
        """
        A post can be unhidden by a moderator who hid the post
        """
        thread = make_only_thread(
            self.regular_user, self.category, visible=False
        )
        self.moderator2.hidden_threads.add(thread)

        comment = make_comment(self.regular_user, thread, visible=False)
        self.moderator2.hidden_comments.add(comment)

        self.assertTrue(self.moderator2.can_unhide_post(thread))
        self.assertTrue(self.moderator2.can_unhide_post(comment))


    def test_can_unhide_post_with_supermoderator_to_owner(self):
        """
        A post can be unhidden by a supermoderator who did not hide the post
        but moderating the post.
        """
        thread = make_only_thread(
            self.user, self.category, visible=False
        )
        self.moderator.hidden_threads.add(thread)
        comment = make_comment(self.user, thread, visible=False)
        self.moderator.hidden_comments.add(comment)

        self.assertTrue(self.supermoderator.can_unhide_post(thread))
        self.assertTrue(self.supermoderator.can_unhide_post(comment))
    
    def test_get_common_categories(self):        
        cats = self.moderator.get_common_categories(self.moderator)
        # self.assertQuerysetEqual(cats, self.moderator.categories.all())

        cats = self.moderator2.get_common_categories(self.moderator)
        # self.assertQuerysetEqual(cats, self.moderator2.categories.all())

        random_category = make_category(title="random")
        self.moderator3.categories.add(random_category)
        self.supermoderator.categories.add(random_category)

        cats = self.moderator3.get_common_categories(self.supermoderator)
        self.assertIn(random_category, cats)
        self.assertNotIn(self.category, cats)
        self.assertNotIn(self.category2, cats)
