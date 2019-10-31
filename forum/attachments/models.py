
import os
import uuid

from django.db import models

from django.utils.crypto import get_random_string
from django.utils.text import slugify
from django.core.files.storage import FileSystemStorage


from forum.comments.models import Comment
from forum.core.models import TimeStampedModel
from forum.threads.models import Thread
from forum.accounts.models import UserProfile


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
    if instance.has_userprofile:
        return "avatars/{final_filename}".format(
            final_filename=final_filename
        )
    return "uploads/{final_filename}".format(
        final_filename=final_filename
    )


class Attachment(models.Model):
    image = models.ImageField(
        upload_to=upload_to, storage=MediaFileSystemStorage()
    )
    filename = models.CharField(max_length=255)    
    url = models.URLField(max_length=2000, blank=True)
    comments = models.ManyToManyField(Comment, blank=True)
    threads = models.ManyToManyField(Thread, blank=True)
    userprofiles = models.ManyToManyField(UserProfile, blank=True)
    md5sum = models.CharField(max_length=36, blank=True)
    has_userprofile = models.BooleanField(default=False)
    is_orphaned = models.BooleanField(default=True)
    
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

        



