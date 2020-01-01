from django.contrib import admin

from .models import Moderator, ModeratorEvent


admin.site.register(Moderator)
admin.site.register(ModeratorEvent)

