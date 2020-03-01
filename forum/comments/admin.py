from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from forum.comments.models import Comment, CommentRevision


class CommentInline(admin.TabularInline):
    model = CommentRevision

class CommentAdmin(admin.ModelAdmin):
    inlines = [
        CommentInline,
    ]
    
admin.site.register(Comment, CommentAdmin)
