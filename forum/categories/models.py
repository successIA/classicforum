from django.db import models
from django.core.urlresolvers import reverse
# from django.conf import settings
# from django.db.models.signals import pre_save
from django.utils.text import slugify
# from django.contrib.contenttypes.fields import GenericRelation

# from django.utils.html import mark_safe
from forum.core.models import TimeStampedModel

# import random
# import string


class CategoryQuerySet(models.query.QuerySet):
    def get_by_slug(self, slug):
        return self.filter(slug=slug).first()


class Category(TimeStampedModel):
    title = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(blank=True)
    description = models.TextField(max_length=300)
    views = models.PositiveIntegerField(default=0)
    icon = models.CharField(max_length=32, blank=True)
    objects = CategoryQuerySet.as_manager()

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Category, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('categories:category_detail', kwargs={'slug': self.slug})
        # return reverse('categories:category_detail', kwargs={'slug': self.slug})

    def get_thread_create_url(self):
        return reverse('thread_create', kwargs={'slug': self.slug})

    def get_thread_form_action(self, filter_str, page):
        return '%s#comment-form' % reverse(
            'categories:category_thread_create',
            kwargs={'slug': self.slug, 'filter_str': filter_str, 'page': page}
        )


# def create_category_slug(instance, new_slug=None):

#     if instance.slug:
#         slug = slugify(instance.slug)
#     else:
#         slug = slugify(instance.title)

#     if new_slug is not None:
#         slug = new_slug
#     qs = Category.objects.filter(slug=slug)
#     if qs.exists():
#         s = ''.join([random.choice(string.ascii_lowercase + string.digits)
#                      for i in range(10)])
#         new_slug = '%s-%s' % (slug, s)
#         return create_category_slug(instance, new_slug=new_slug)
#     return slug


# def pre_save_category_receiver(sender, instance, *args, **kwargs):
#     instance.slug = create_category_slug(instance)


# pre_save.connect(pre_save_category_receiver, sender=Category)
