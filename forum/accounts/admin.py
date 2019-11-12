from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from forum.accounts.models import User
from forum.threads.models import Thread, ThreadFollowership


class ThreadInline(admin.TabularInline):
    model = Thread


class ThreadFollowershipInline(admin.TabularInline):
    model = ThreadFollowership


# class FollowersInline(admin.TabularInline):
#     model =


# class ForumUserAdmin(UserAdmin):
#     model = User
#     list_display = [
#         'username',
#         'gender',
#         'signature',
#         'location',
#         'website',
#         # 'followers',
#         # 'following',
#         'last_seen',
#         'email_confirmed',
#         'avatar_url',
#     ]


admin.site.register(User, UserAdmin)
