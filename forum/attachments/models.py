import os
import uuid

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.text import slugify

from forum.attachments.utils import (
    get_image_srcs_from_msg,
    get_unref_image_srcs_in_msg,
    md5,
)
from forum.core.models import TimeStampedModel


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
    def synchronise(self, comment, prev_msg=None):
        if prev_msg:
            self._remove_comment_from_attachment(comment, prev_msg)
        src_list = get_image_srcs_from_msg(comment.message)

        for url in src_list:
            att_list = None
            if url:
                att_list = list(self.filter(url=url))
            if att_list:
                att = att_list[0]
                att.comments.add(comment)
                att.is_orphaned = False
                att.save()

    def _remove_comment_from_attachment(self, comment, prev_msg):
        '''
        Detach comment from all its attachments if there is any
        change in the image urls in the message
        '''
        unreferenced_image_sources = get_unref_image_srcs_in_msg(
            prev_msg, comment.message
        )
        for att in comment.attachment_set.all():
            if att.url in unreferenced_image_sources:
                att.comments.remove(comment)
                if not att.is_avatar and att.comments.count() == 0:
                    att.is_orphaned = True
                    att.save()

    def _update_users(self, user):
        qs = self.filter(url=user.avatar_url, is_avatar=True)[:1]
        attachment = qs[0] if qs else None
        if attachment:
            attachment.users.remove(user)
            if attachment.users.count() == 0:
                attachment.is_orphaned = True
                attachment.save()


    def create_avatar(self, image, user):
        if image:
            if user.avatar_url:
                self._update_users(user)
            
            md5sum = md5(image)
            qs = self.filter(md5sum=md5sum, is_avatar=True)[:1]
            attachment = qs[0] if qs else None
            if attachment:
                if attachment.is_orphaned:
                    attachment.is_orphaned = False
                    attachment.save()
                attachment.users.add(user)
                return attachment.url
            else:
                attachment = self.create(
                    image=image, 
                    filename=image.name, 
                    is_avatar=True, 
                    is_orphaned=False
                )
                attachment.users.add(user)
                return attachment.url
        return None


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
