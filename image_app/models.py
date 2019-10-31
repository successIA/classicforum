from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


def image_upload_to(instance, filename):
    self = instance
    heading = None
    try:
        heading = self.content_object.slug
    except AttributeError:
        heading = self.content_object.user.username
    if heading is None:
        raise ValueError
    basename, file_extension = filename.split(".")
    new_filename = "%s.%s" % (basename, file_extension)
    return (self.content_object.__class__.__name__ + '_images').lower() + "/%s/%s" % (heading, new_filename)


class Image(models.Model):
    image = models.ImageField(upload_to=image_upload_to)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.pk)
