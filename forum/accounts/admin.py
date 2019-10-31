from django.contrib import admin

from forum.accounts.models import UserProfile
from forum.threads.models import  Thread, ThreadFollowership


class ThreadInline(admin.TabularInline):
    model = Thread

class ThreadFollowershipInline(admin.TabularInline):
    model = ThreadFollowership

class UserProfileAdmin(admin.ModelAdmin):
    inlines = [
        # ThreadInline,
        # ThreadFollowershipInline
    ]


admin.site.register(UserProfile, UserProfileAdmin)
