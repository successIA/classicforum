from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from forum.comments.models import Comment
from forum.threads.models import (
    Thread,
    ThreadRevision,
    ThreadFollowership
)


class ThreadRevisionInline(admin.TabularInline):
    model = ThreadRevision


class CommentInline(admin.TabularInline):
    model = Comment


# class ThreadAdmin(admin.ModelAdmin):
#     inlines = [
#         ThreadFollowershipInline,
#         # ThreadRevisionInline,
#         # CommentInline
#     ]
    # raw_id_fields = ('user', 'category', 'final_comment_user')

class ThreadAdmin(admin.ModelAdmin):
    inlines = [
        CommentInline
    ]


admin.site.register(Thread, ThreadAdmin)
admin.site.register(ThreadRevision)
admin.site.register(ThreadFollowership)
