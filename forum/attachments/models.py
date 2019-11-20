import os
import uuid

from django.db import models
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from forum.core.models import TimeStampedModel
from forum.attachments.utils import get_image_sources_from_message
from forum.attachments.utils import (
    get_unreferenced_image_srcs_in_message
)
from forum.attachments.utils import md5


class MediaFileSystemStorage(FileSystemStorage):
    pass


def get_extension(filepath):
    base_name = os.path.basename(filepath)
    name, extension = os.path.splitext(base_name)
    return extension


def upload_to(instance, filename):
    extension = get_extension(filename)
    new_filename = instance.md5sum
    final_filename = new_filename + extension
    if instance.is_avatar:
        return "avatars/%s" % final_filename
    return "uploads/%s" % final_filename


class AttachmentQuerySet(models.query.QuerySet):

    def sync_with_comment(self, comment, previous_message=None):
        if previous_message:
            self._remove_comment_from_instance(comment, previous_message)
        image_url_list = get_image_sources_from_message(comment.message)

        for url in image_url_list:
            url = url.replace('http://127.0.0.1:8000', "")
            instance_list = None
            if url:
                instance_list = list(self.filter(url=url))
            if instance_list:
                instance = instance_list[0]
                instance.comments.add(comment)
                instance.is_orphaned = False
                instance.save()

    def _remove_comment_from_instance(self, comment, previous_message):
        '''
        Detach comment from all its attachments if there is any
        change in the image urls in the message
        '''
        unreferenced_image_sources = get_unreferenced_image_srcs_in_message(
            previous_message, comment.message
        )
        for instance in comment.attachment_set.all():
            url_with_domain = 'http://127.0.0.1:8000%s' % instance.url
            if url_with_domain in unreferenced_image_sources:
                instance.comments.remove(comment)
                if not instance.is_avatar and instance.comments.count() == 0:
                    instance.is_orphaned = True
                    instance.save()

    def create_avatar(self, image, user):
        if not image:
            return
        md5sum = md5(image)
        queryset_list = list(self.filter(md5sum=md5sum, is_avatar=True))
        if queryset_list:
            queryset_list[0].users.add(user)
            return queryset_list[0].image.url
        else:
            instance = self.create(
                image=image, filename=image.name, is_avatar=True
            )
            instance.users.add(user)
            return instance.image.url


class Attachment(models.Model):
    image = models.ImageField(
        upload_to=upload_to
        # , storage=MediaFileSystemStorage()
    )
    url = models.URLField(max_length=2000, blank=True)
    filename = models.CharField(max_length=255)
    comments = models.ManyToManyField('comments.Comment', blank=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    md5sum = models.CharField(max_length=36, blank=True)
    is_avatar = models.BooleanField(default=False)
    is_orphaned = models.BooleanField(default=True)
    objects = AttachmentQuerySet.as_manager()

    def __str__(self):
        return str(self.filename)

    def save(self, *args, **kwargs):

        if not self.pk and not self.md5sum:  # file is new
            self.md5sum = md5(self.image)
        self.filename = self.image.name
        super().save(*args, **kwargs)
        self.url = self.image.url
        kwargs['force_update'] = True
        kwargs['force_insert'] = False
        super().save(*args, **kwargs)
