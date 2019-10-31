# from django.db import models
# from django.conf import settings

# from forum.threads.models import Thread
# from forum.comments.models import Comment

# from forum.core.models import TimeStampedModel


# # Notification(sender='aia99', receiver='janet', notif_type='COMMENT_UPVOTED', comment_id=1, unread=False)

# # Notification(sender='john', receiver='janet', notif_type='COMMENT_UPVOTED', comment_id=1, unread=False)

# # Notification(sender='abdullah', receiver='janet', notif_type='COMMENT_UPVOTED', comment_id=1, unread=False)

# # Notification(sender='abdullah', receiver='janet', notif_type='COMMENT_REPLY', comment_id=1, unread=False)


# # notif = Notification.objects.filter(receiver='janet', unread='False').annotate(count=Count('activity_type'), max=Max('created'))


# # notif.sender and notif.count notif.activity_type your
# # if notif.comment:
# #   notif.comment.get_precise_url
# # if notif.thread:
# #   notif.thread.get_precise_url


# # Notification(sender='abdullah', receiver='janet', notif_type='THREAD_UPDATED', thread_id=1, unread=False)



# # COMMENT_CREATE
# # COMMENT_REPLY
# # COMMENT_UPDATE
# # COMMENT_UPVOTE
# # COMMENT_DOWNVOTE
# # THREAD CREATE
# # THREAD UPDATE
# # THREAD_FOLLOWING
# # THREAD_UNFOLLOW
# # USER_FOLLOW
# # USER_UNFOLLOW


# # Activity(actor='janet', activity_type='COMMENT_UPVOTED', comment_id=1)
# # Activity(actor='janet', activity_type='THREAD_UPDATE', thread_id=1)
# # Activity(actor='janet', activity_type='USER_UNFOLLOW', user_id=1)

# # Activity.objects.filter(actor='janet')
# # You activity.action(posted) posted a activity.type (reply) comment.get_precise_url
# # You activity.action(updated) a thread thread.get_precise_url
# # You followed thread
# # You unfollowed thread
# # You upvoted comment
# # You followed user


# # activity.get_description(self):
# #     if activity.comment:
# #         return activity.comment.get_activity_description(activity.type)
# #     elif activity.thread:
# #         return activity.thread.get_activity_description(activity.type)
# #     elif activity.user:
# #         return activity.user.get_activity_description(activity.type)



# # def get_activity_description(type):
# #     if type == Activity.COMMENT_UPVOTED:
# #         return 'You upvoted a reply' + self.get_precise_url + ' in ' + self.thread.title
# #     elif type == Activity.COMMENT_CREATED:
# #         return 'You posted a reply' + self.get_precise_url + ' in ' + self.thread.title


# # def get_description(self):
# #     if self.

# class Notification(TimeStampedModel):
#     THREAD_FOLLOWING = 'THREAD_FOLLOWING'
#     THREAD_LIKED = 'THREAD_LIKED'
#     THREAD_COMMENTED = 'THREAD_COMMENTED'
#     THREAD_UPDATED = 'THREAD_UPDATED'
#     COMMENT_LIKED = 'COMMENT_LIKED'
#     COMMENT_REPLIED = 'COMMENT_REPLIED'
#     COMMENT_EDITED = 'COMMENT_EDITED'

#     ACCOUNT_UPDATE = 'ACCOUNT_UPDATE'
#     COMMENT_UPVOTE = 'COMMENT_UPVOTE'
#     COMMENT_DOWNVOTE = 'COMMENT_DOWNVOTE'
#     USER_FOLLOWING = 'USER_FOLLOWING'
#     THREAD_FOLLOWING = 'THREAD_FOLLOWING'




#     NOTIFICATION_TYPES = (
#         (THREAD_FOLLOWING , THREAD_FOLLOWING),
#         (THREAD_LIKED, THREAD_LIKED),
#         (THREAD_COMMENTED, THREAD_COMMENTED),
#         (THREAD_UPDATED, THREAD_UPDATED),
#         (COMMENT_LIKED, COMMENT_LIKED),
#         (COMMENT_REPLIED, COMMENT_REPLIED),
#         (COMMENT_EDITED, COMMENT_EDITED)
#     )
#     thread = models.ForeignKey(Thread, on_delete=models.CASCADE, null=True)
#     comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True)
#     sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notif_sender', null=True)
#     receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notif_receiver', null=True)
#     notification_type = models.CharField(max_length=18, choices=NOTIFICATION_TYPES)
#     unread = models.BooleanField(default=True)
#     is_final_thread = models.BooleanField(default=False)
#     objects = NotificationQuerySet.as_manager()
    
#     def __str__(self):
#         return 'thread #' + str(self.thread.id) + ' comment #: ' + str(self.comment.id) + ' receiver: ' + self.receiver.username
