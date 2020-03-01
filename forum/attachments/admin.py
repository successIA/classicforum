from django import forms
from django.contrib import admin
from django.db import models

from .models import Attachment

admin.site.register(Attachment)
