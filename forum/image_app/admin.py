from django.contrib import admin
from django import forms

from .models import Image
from django.db import models


# class ImageAdmin(admin.ModelAdmin):
#     formfield_overrides = {
#         models.ImageField: {'widget': forms.ClearableFileInput(attrs={'multiple': True})}
#     }


admin.site.register(Image)
