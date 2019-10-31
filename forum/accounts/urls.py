from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.urls import reverse, reverse_lazy

from forum.accounts.views import (
    signup, 
    account_activation_sent,
    activate,
    user_profile_edit, 
    user_profile_stats, 
    user_comment_list,
    follow_user,
    user_following,
    user_followers,
    user_notification_list,
    user_mention,
    user_mention_list,
    user_thread_list,
)

from forum.accounts.forms import UserPasswordChangeForm

urlpatterns = [
    # authentication
    url(r'account_activation_sent/$', account_activation_sent, name='account_activation_sent'),

    url(r'activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        activate, name='activate'),

    url(r'auth/signup/$', signup, name='signup'),
    url(r'auth/login/$', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    url(r'auth/logout/$', auth_views.LogoutView.as_view(), name='logout'),

    url(
        r'auth/reset/$',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
            success_url = reverse_lazy('accounts:password_reset_done')
        ),
        name='password_reset'
    ),

    url(
        r'auth/reset/done/$',
        auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
        name='password_reset_done'
    ),

    url(
        r'auth/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html', 
            success_url = reverse_lazy('accounts:password_reset_complete') 
        ),
        name='password_reset_confirm'
    ),

    url(r'auth/reset/complete/$',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

    # url(r'settings/account/$', accounts_views.UserUpdateView.as_view(), name='my_account'),
    url(
        r'auth/settings/password/$',
        auth_views.PasswordChangeView.as_view(
            form_class=UserPasswordChangeForm,
            template_name='accounts/password_change.html',
            success_url = reverse_lazy('accounts:password_change_done')
        ),
        name='password_change'
    ),

    url(
        r'auth/settings/password/done/$',
        auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'),
        name='password_change_done'
    ),

    # userprofile
    url(r'users/mention/$', user_mention, name='user_mention'),
    url(r'users/mention-list/$', user_mention_list, name='user_mention_list'),

    # url(r'(?P<username>[\w-]+)/new/(?P<page>[\d]*)?/?$', UserNewThreadsView.as_view(), name='thread_new'),
    # url(r'(?P<username>[\w-]+)/following/(?P<page>[\d]*)?/?$', UserFollowingThreadsView.as_view(), name='thread_following'),
    # url(r'(?P<username>[\w-]+)/me/(?P<page>[\d]*)?/?$', UserThreadsView.as_view(), name='thread_user'),

    url(r'(?P<username>[\w-]+)/(?P<filter_str>new)/(?P<page>[\d]*)?/?$', user_thread_list, name='thread_new'),
    url(r'(?P<username>[\w-]+)/(?P<filter_str>following)/(?P<page>[\d]*)?/?$', user_thread_list, name='thread_following'),
    url(r'(?P<username>[\w-]+)/(?P<filter_str>me)/(?P<page>[\d]*)?/?$', user_thread_list, name='thread_user'),


    url(r'(?P<username>[\w-]+)/info/$', user_profile_edit, name='user_edit'),
    
    url(r'(?P<username>[\w-]+)/follow/$', follow_user, name='user_follow'),
    url(r'(?P<username>[\w-]+)/user-following/$', user_following, name='user_following'),
    url(r'(?P<username>[\w-]+)/user-followers/$', user_followers, name='user_followers'),
    url(r'(?P<username>[\w-]+)/comments/(?P<page>[\d]*)?/?$', user_comment_list, name='user_comments'),
    url(r'(?P<username>[\w-]+)/notifications/$', user_notification_list, name='user_notifs'),
    url(r'(?P<username>[\w-]+)/$', user_profile_stats, name='user_stats'),

    # url(r'(?P<username>[\w-]+)/(?P<filter>[\w-]+)/(?P<page>[\d]*)?/?$', user_thread_list.as_view(), name='thread_user'),

]
