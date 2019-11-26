from background_task import background
from forum.threads.models import Thread, ThreadFollowership
from forum.attachments.models import Attachment


# @background(schedule=3)
# def create_thread_activities(thread_id, comment_id):
#     from forum.comments.models import Comment
#     print('TASK ACTIVITY CALLED')
#     thread_qs = Thread.objects.filter(pk=thread_id)
#     comment_qs = Comment.objects.filter(pk=comment_id)
#     if thread_qs and comment_qs:
#         ThreadActivity.objects.create_activities(thread_qs[0], comment_qs[0])

@background(schedule=3)
def sync_comment_with_thread_followership(thread_id, comment_id):
    from forum.comments.models import Comment

    print('TASK THREAD FOLLOWERSHIP CALLED')
    thread_qs = Thread.objects.filter(pk=thread_id)
    comment_qs = Comment.objects.filter(pk=comment_id)
    if thread_qs and comment_qs:
        ThreadFollowership.objects.sync_with_comment(
            thread_qs[0], comment_qs[0]
        )


@background(schedule=6)
def sync_attachment_with_comment(comment_id, message=None):
    from forum.comments.models import Comment
    print('TASK SYNC ATTACHMENT CALLED')
    comment_qs = Comment.objects.filter(pk=comment_id)
    if comment_qs:
        Attachment.objects.sync_with_comment(comment_qs[0], message)
