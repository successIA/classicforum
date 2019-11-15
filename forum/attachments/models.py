import os
import uuid

from django.db import models
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from forum.core.models import TimeStampedModel
from forum.attachments.utils import find_images_in_message
from forum.attachments.utils import (
    get_unreferenced_image_srcs_in_message
)
from forum.attachments.utils import md5


class MediaFileSystemStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        if max_length and len(name) > max_length:
            raise(Exception("name's length is greater than max_length"))
        return name

    def _save(self, name, content):
        if self.exists(name):
            # if the file exists, do not call the superclasses _save method
            return name
        # if the file is new, DO call it
        return super(MediaFileSystemStorage, self)._save(name, content)


def get_filename_ext(filepath):
    base_name = os.path.basename(filepath)
    name, ext = os.path.splitext(base_name)
    return name, ext


def upload_to(instance, filename):
    name, ext = get_filename_ext(filename)
    new_filename = instance.md5sum
    final_filename = '{new_filename}{ext}'.format(
        new_filename=new_filename, ext=ext
    )
    if instance.is_avatar:
        return "avatars/{final_filename}".format(
            final_filename=final_filename
        )
    return "uploads/{final_filename}".format(
        final_filename=final_filename
    )


class AttachmentQuerySet(models.query.QuerySet):
    def sync_with_comment(self, comment, prev_message=None):
        if prev_message:
            self._detach_from_comment(comment, prev_message)
        image_url_list = find_images_in_message(comment.message)
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

    def _detach_from_comment(self, comment, prev_message):
        '''
        Detach comment from all its attachments if there is any
        change in the image urls in the message
        '''
        urls = get_unreferenced_image_srcs_in_message(
            prev_message, comment.message
        )
        for instance in comment.attachment_set.all():
            if instance.url in urls:
                instance.comments.remove(comment)
                count = instance.comments.count()
                is_avatar = instance.is_avatar
                if not is_avatar and count < 1:
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
        upload_to=upload_to, storage=MediaFileSystemStorage()
    )
    filename = models.CharField(max_length=255)
    url = models.URLField(max_length=2000, blank=True)
    comments = models.ManyToManyField('comments.Comment', blank=True)
    # threads = models.ManyToManyField("threads.Thread", blank=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    md5sum = models.CharField(max_length=36, blank=True)
    is_avatar = models.BooleanField(default=False)
    is_orphaned = models.BooleanField(default=True)
    objects = AttachmentQuerySet.as_manager()

    def __str__(self):
        return str(self.filename)

    def save(self, *args, **kwargs):
        from hashlib import md5
        if not self.pk:  # file is new
            md5 = md5()
            for chunk in self.image.chunks():
                md5.update(chunk)
            self.md5sum = md5.hexdigest()
        self.filename = self.image.name
        super().save(*args, **kwargs)
        self.url = self.image.url
        super().save(*args, **kwargs)
