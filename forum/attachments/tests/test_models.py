import os
import shutil

from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from test_plus import TestCase

from forum.attachments.models import (
    Attachment, upload_to # MediaFileSystemStorage,
)
# from forum.attachments.models import upload_to

from forum.comments.models import Comment, CommentRevision
from forum.comments.tests.utils import make_comment
from forum.threads.tests.utils import make_only_thread
from forum.categories.tests.utils import make_category

TEST_IMAGES_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'testimages'
)
TEST_IMAGE_1 = os.path.join(TEST_IMAGES_DIR, 'abu3.jpg')
TEST_IMAGE_2 = os.path.join(TEST_IMAGES_DIR, 'aprf1.jpg')

AVATAR_UPLOAD_DIR = os.path.join(settings.TEST_MEDIA_ROOT, 'avatars')


@override_settings(MEDIA_ROOT=settings.TEST_MEDIA_ROOT)
class AttachmentModelTest(TestCase):
    def setUp(self):
        self.test_image = SimpleUploadedFile(
            name='abu3.jpg',
            content=open(TEST_IMAGE_1, 'rb').read(),
            content_type='image/jpeg'
        )

    def tearDown(self):
        self.test_image.close()
        try:
            if os.path.isdir(settings.TEST_MEDIA_ROOT):
                shutil.rmtree(settings.TEST_MEDIA_ROOT)
        except Exception as e:
            print(e)

    def test_save(self):
        attachment = Attachment.objects.create(image=self.test_image)
        self.assertIsNotNone(attachment.md5sum)
        self.assertEquals(attachment.filename, 'abu3.jpg')
        self.assertIsInstance(attachment, Attachment)

    def test_upload_to(self):
        attachment = Attachment(image=self.test_image, md5sum='abc')
        returned_upload_to = upload_to(attachment, attachment.filename)
        expected_upload_to = 'uploads/%s' % 'abc'
        self.assertEquals(returned_upload_to, expected_upload_to)

    def test_upload_to_with_avatar(self):
        attachment = Attachment(
            image=self.test_image, md5sum='abc', is_avatar=True
        )
        returned_upload_to = upload_to(attachment, attachment.filename)
        expected_upload_to = 'avatars/%s' % 'abc'
        self.assertEquals(returned_upload_to, expected_upload_to)

# @override_settings(MEDIA_ROOT=settings.TEST_MEDIA_ROOT)
# class MediaFileSystemStorageTest(TestCase):
#     def setUp(self):
#         self.storage = MediaFileSystemStorage()
#         self.test_image = SimpleUploadedFile(
#             name='abu3.jpg',
#             content=open(TEST_IMAGE_1, 'rb').read(),
#             content_type='image/jpeg'
#         )
#         self.attachment = Attachment(image=self.test_image)

#     def tearDown(self):
#         self.test_image.close()
#         try:
#             if os.path.isdir(settings.TEST_MEDIA_ROOT):
#                 shutil.rmtree(settings.TEST_MEDIA_ROOT)
#         except Exception as e:
#             print(e)

#
#     def test_save(self):
#         result1 = self.storage._save(
#             self.attachment.image.name, self.attachment.image
#         )
#         print('RESULT1:', result1)
#         print('IMAGE_NAME:', self.attachment.image.name)
#         self.assertEquals(result1, self.attachment.image.name)

#         result2 = self.storage._save(
#             self.attachment.image.name, self.attachment.image
#         )
#         print('RESULT2:', result2)
#         print('IMAGE_NAME:', self.attachment.image.name)
#         self.assertEquals(result2, self.attachment.image.name)


@override_settings(MEDIA_ROOT=settings.TEST_MEDIA_ROOT)
class AttachmentQuerySetTest(TestCase):
    def setUp(self):
        self.user = self.make_user('john')
        self.test_image = SimpleUploadedFile(
            name='abu3.jpg',
            content=open(TEST_IMAGE_1, 'rb').read(),
            content_type='image/jpeg'
        )
        self.test_image2 = SimpleUploadedFile(
            name='aprf1.jpg',
            content=open(TEST_IMAGE_2, 'rb').read(),
            content_type='image/jpeg'
        )
        self.current_count = Attachment.objects.count()

    def tearDown(self):
        self.test_image.close()
        self.test_image2.close()
        try:
            if os.path.isdir(settings.TEST_MEDIA_ROOT):
                shutil.rmtree(settings.TEST_MEDIA_ROOT)
        except Exception as e:
            print(e)

    def test_create_avatar_with_no_image(self):
        url = Attachment.objects.create_avatar(None, self.user)
        self.assertEquals(Attachment.objects.count(), self.current_count)
        self.assertIsNone(url)

    def test_create_avatar_with_image(self):
        url = Attachment.objects.create_avatar(self.test_image, self.user)
        self.assertEquals(Attachment.objects.count(), self.current_count + 1)
        self.assertEquals(Attachment.objects.all().first().image.url, url)
        self.assertIn(self.user, Attachment.objects.all().first().users.all())

    def test_create_avatar_with_duplicate_images(self):
        second_user = self.make_user('second_user')

        url = Attachment.objects.create_avatar(self.test_image, self.user)
        url2 = Attachment.objects.create_avatar(self.test_image, second_user)

        self.assertEquals(Attachment.objects.count(), self.current_count + 1)
        path, dirs, files = next(os.walk(AVATAR_UPLOAD_DIR))
        self.assertEquals(len(files), 1)
        self.assertEquals(url, url2)
        self.assertIn(self.user, Attachment.objects.all().first().users.all())
        self.assertIn(
            second_user, Attachment.objects.all().first().users.all()
        )

    
    def test_synchronise(self):
        attachment = Attachment.objects.create(image=self.test_image)
        category = make_category()
        thread = make_only_thread(self.user, category)

        message = f'![]({attachment.image.url})'
        comment = make_comment(self.user, thread, message=message)
        Attachment.objects.synchronise(comment)
        self.assertIn(
            comment, Attachment.objects.all().first().comments.all()
        )
        self.assertFalse(Attachment.objects.last().is_orphaned)
    
    def test_synchronise_with_revision(self):
        attachment = Attachment.objects.create(image=self.test_image)
        category = make_category()
        thread = make_only_thread(self.user, category)

        message = f'![]({attachment.image.url})'
        comment = make_comment(self.user, thread, message=message)
        Attachment.objects.synchronise(comment)
        self.assertIn(
            comment, Attachment.objects.all().first().comments.all()
        )
        self.assertFalse(Attachment.objects.last().is_orphaned)

        Comment.objects.filter(pk=comment.pk).update(
            message='No more image source'
        )
        revision = CommentRevision.objects.create(
            comment=comment, message=comment.message
        )
        comment.refresh_from_db()
        Attachment.objects.synchronise(comment, revision.message)
        self.assertNotIn(
            comment, Attachment.objects.all().first().comments.all()
        )
        self.assertTrue(Attachment.objects.last().is_orphaned)