from django.db import models
from django.core.urlresolvers import reverse
from django.utils.text import slugify
from forum.core.models import TimeStampedModel

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
    
    def get_precise_url(self, filter_str, page):
        return reverse(
            "categories:category_detail_filter",
            kwargs={'slug': self.slug,
                    'filter_str': filter_str, 'page': page}
        )

    def get_thread_create_url(self):
        return reverse('thread_create', kwargs={'slug': self.slug})

    def get_thread_form_action(self, filter_str, page):
        return '%s#comment-form' % reverse(
            'categories:category_thread_create',
            kwargs={'slug': self.slug, 'filter_str': filter_str, 'page': page}
        )
