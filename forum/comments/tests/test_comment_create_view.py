from django.core.urlresolvers import reverse, resolve
from django.test.client import RequestFactory
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile



from forum.categories.models import Category
from forum.threads.models import Thread, ThreadFollowership
from forum.comments.models import Comment
from forum.comments.views import CommentCreateView, CommentQuoteView
from forum.comments.forms import CommentForm
from forum import testutils
from forum.attachments.models import Attachment


import os


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath('__file__')))

image_path = os.path.join(BASE_DIR, 'forum_project', 'forum', 'comments', 'tests', 'images', 'marketing1.jpg')
image_path2 = os.path.join(BASE_DIR, 'forum_project', 'forum','comments', 'tests', 'images', 'abu3.jpg')

img_dir = os.path.join(BASE_DIR, 'forum_project', 'forum', 'media', 'tests')


class CommentTest(TestCase):
    def setUp(self):
        testutils.sign_up_a_new_user(self, 'john')
        self.user = User.objects.get(id=1)
        self.category = Category.objects.create(title='Django', description='The Web Framework For The Perfectionist', slug='django')
        self.thread = Thread.objects.create(title='Galaxy S5 Discussion Thread', body='Lorem ipsum dalor', category=self.category, user=self.user)
        self.image = SimpleUploadedFile(name='test_image.jpg', content=open(image_path, 'rb').read(), content_type='image/jpeg')
        self.image2 = SimpleUploadedFile(name='test_image2.jpg', content=open(image_path2, 'rb').read(), content_type='image/jpeg')


class CommentCreateTest(CommentTest):

    def setUp(self):
        super().setUp()
        self.comment = Comment.objects.create(message='python is awesome', thread=self.thread, user=self.user)
        self.response = self.client.get(self.thread.get_comment_create_url())

    def test_unautheticated_user_cannot_see_the_comment_page(self):
        self.client.logout()
        self.response = self.client.get(self.thread.get_comment_create_url())
        self.assertEquals(self.response.status_code, 302)

    def test_comment_edit_view_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_a_comment_edit_view_function_with_thread_slug(self):
        view = resolve(self.thread.get_comment_create_url())
        self.assertEquals(view.func.view_class, CommentCreateView)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_comment_form_context_fields(self):
        self.assertContains(self.response, '<input', 4)
        self.assertContains(self.response, 'type="text"', 1)
        self.assertContains(self.response, "type='hidden'", 2)
        self.assertContains(self.response, '<textarea', 1)
        self.assertContains(self.response, 'type="file"', 1)
        fields = ['message']
        self.assertTrue(self.response.context.get('form'))
        self.assertEquals(fields, list(self.response.context.get('form').fields))

    def test_a_comment_should_belong_to_a_thread(self):
        self.assertEquals(self.thread.comments.first(), self.comment)

    def test_a_comment_should_belong_to_a_user(self):
        self.assertEquals(self.user.comment_set.first(), self.comment)

    def test_comment_edit_page_has_a_thread_context(self):
        self.assertEqual(self.response.context.get('thread', None), self.thread)

    def test_thread_detail_page_has_a_category_context(self):
        self.assertEqual(self.response.context.get('category', None), self.category)

    def test_a_comment_edit_page_contains_thread_title(self):
        self.assertContains(self.response, self.thread.title)

    # def test_a_comment_edit_page_contains_a_form_context(self):
    #     form_context = self.response.context.get('form')
    #     form = CommentCreateView
    #     self.assertEquals(form, form_context)

    def test_a_comment_edit_page_contains_csrf_(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')


class CommentSubmitTest(CommentTest):
    def setUp(self):
        super().setUp()
        self.message = 'Hello World'
        self.thread_slug = self.thread.slug
        self.response = self.client.post(self.thread.get_comment_create_url(),
                                         {'message': self.message})

    def tearDown(self):        
        # img_path = os.path.join(img_dir, md5(self.image) + '.jpg')
        # # self.test_image.close()
        # if os.path.exists(img_path):
        #     os.remove(img_path)
        folder = os.path.join(img_dir, 'uploads')
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except Exception as e:
                print(e)

    def test_an_autheticated_user_can_submit_a_valid_comment(self):
        comment = Comment.objects.get(message=self.message)
        self.assertEqual(comment.message, self.message)

    def test_an_authenticated_user_can_embed_images_in_comment(self):
        # from django.utils.html import mark_safe
        # from markdown import markdown

        attachment = Attachment(image=self.image)
        attachment2 = Attachment(image=self.image2)

        # Use instance.save instead of Class.objects.create to avoid
        # unique constraint error
        attachment.save()
        attachment2.save()
        fullSrc = '![](http://127.0.0.1:8000' + attachment.url + ')';
        fullSrc2 = '![](http://127.0.0.1:8000' + attachment2.url + ')';
        message = 'Python is simple' + fullSrc + 'Django is cool' + fullSrc2
        # send post data of thread and image
        response = self.client.post(self.thread.get_comment_create_url(), {'message': message}, follow=True)
        self.assertEquals(response.status_code, 200)
        comment = Comment.objects.get(id=2)
        # print(response.content)
        self.assertIn(attachment.url, comment.message)
        self.assertIn(attachment2.url, comment.message)

    def test_comment_with_embeded_images_is_added_to_attachment(self):
        attachment = Attachment(image=self.image)
        attachment2 = Attachment(image=self.image2)

        # Use instance.save instead of Class.objects.create to avoid
        # unique constraint error
        attachment.save()
        attachment2.save()
        fullSrc = '![](http://127.0.0.1:8000' + attachment.url + ')';
        fullSrc2 = '![](http://127.0.0.1:8000' + attachment2.url + ')';
        message = 'Python is simple' + fullSrc + 'Django is cool' + fullSrc2
        # send post data of thread and image
        response = self.client.post(self.thread.get_comment_create_url(), {'message': message}, follow=True)
        self.assertEquals(response.status_code, 200)
        comment = Comment.objects.get(id=2)
        attachment = Attachment.objects.get(id=1)
        attachment2 = Attachment.objects.get(id=2)
        self.assertEquals(attachment.comments.first(), comment)
        self.assertEquals(attachment2.comments.first(), comment)

    def test_existing_embeded_images_are_not_added_to_attachment(self):
        attachment = Attachment(image=self.image)
        attachment2 = Attachment(image=self.image2)

        # Use instance.save instead of Class.objects.create to avoid
        # unique constraint error
        attachment.save()
        attachment2.save()
        fullSrc = '![](http://127.0.0.1:8000' + attachment.url + ')';
        fullSrc2 = '![](http://127.0.0.1:8000' + attachment2.url + ')';
        message = 'Python is simple' + fullSrc + 'Django is cool' + fullSrc2
        # send post data of thread and image
        response = self.client.post(self.thread.get_comment_create_url(), {'message': message}, follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(Attachment.objects.all().count(), 2)
        attachment = Attachment.objects.get(id=1)
        attachment2 = Attachment.objects.get(id=2)
        fullSrc = '![](http://127.0.0.1:8000' + attachment.url + ')';
        fullSrc2 = '![](http://127.0.0.1:8000' + attachment2.url + ')';
        message = 'Python is easy' + fullSrc + 'Django is flexible' + fullSrc2
        response2 = self.client.post(self.thread.get_comment_create_url(), {'message': message}, follow=True)
        self.assertEquals(response2.status_code, 200)
        comment = Comment.objects.get(id=3)
        self.assertEquals(Attachment.objects.all().count(), 2)
        attachment = Attachment.objects.get(id=1)
        attachment2 = Attachment.objects.get(id=2)
        self.assertEquals(attachment.comments.filter(id=3).first(), comment)
        self.assertEquals(attachment2.comments.filter(id=3).first(), comment)




        



    def test_authenticated_user_cannot_submit_an_invalid_comment(self):
        self.client.post(self.thread.get_comment_create_url(),
                         {'message': ''})
        self.assertTemplateUsed('comment_form.html')
        self.client.post(self.thread.get_comment_create_url(),
                         {'message': {}})
        self.assertTemplateUsed('comment_form.html')

    def test_valid_comment_status_code(self):
        # redirect to success url
        self.assertEquals(self.response.status_code, 302)

    def test_an_unauthenticated_user_cannot_submit_a_reply(self):
        self.client.logout()
        response = self.client.post(self.thread.get_comment_create_url(),
                                    {'message': self.message})
        # redirect back
        self.assertEquals(response.status_code, 302)

    def test_an_unauthenticated_user_post_submit_should_not_be_in_the_database(self):
        comment = None
        try:
            # look for the posted comment in the databse
            comment = Comment.objects.get(message=self.message)
        except:
            self.assertEquals(comment, None)

    def test_an_authenticated_user_becomes_a_follower_of_a_thread_after_commenting(self):
        userprofile = self.user.userprofile
        t_fship = ThreadFollowership.objects.filter(
                    userprofile=userprofile, thread=self.thread
                  ).first()
        self.assertEquals(t_fship.thread, self.thread)






