from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from forum.comments.models import Comment
from forum.image_app.models import Image
from forum.threads.models import (
    Thread, 
    ThreadFollowership, 
    ThreadRevision
)



class ThreadFollowershipInline(admin.TabularInline):
    model = ThreadFollowership


class ThreadRevisionInline(admin.TabularInline):
    model = ThreadRevision


class CommentInline(admin.TabularInline):
    model = Comment

# class ImageInline(GenericTabularInline):
#     model = Image
#     extra = 0
#     max_num = 5


class ThreadAdmin(admin.ModelAdmin):
    inlines = [
        ThreadFollowershipInline,
        # ThreadRevisionInline,
        # CommentInline
    ]
    # raw_id_fields = ('user', 'category', 'final_comment_user')


admin.site.register(Thread, ThreadAdmin)
admin.site.register(ThreadFollowership)

#     # prepopulated_fields = {"slug": ("title",)}

#     # def save_model(self, request, obj, form, change):
#     #     slug = create_category_slug(obj)
#     #     obj.slug = slug
#     #     super(ArticleAdmin, self).save_model(request, obj, form, change)


# class ThreadAdmin(admin.ModelAdmin):
#     prepopulated_fields = {"slug": ("title",)}


# def create_category_slug(instance, new_slug=None):
#     slug = slugify(instance.title)
#     if new_slug is not None:
#         slug = new_slug
#     qs = Category.objects.filter(slug=slug).order_by('-id')
#     exists = qs.exists()
#     if exists:
#         new_slug = '%s-%s' % (slug, qs.first().id)
#         return create_category_slug(instance, new_slug=new_slug)
#     return slug
