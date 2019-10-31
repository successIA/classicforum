from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from forum.categories.models import Category

admin.site.register(Category)
