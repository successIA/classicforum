from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from forum.accounts.models import User


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
