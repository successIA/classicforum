from django.utils import timezone

from faker import Faker

from forum.comments.models import Comment

fake = Faker()


def make_comment(
    user, thread, is_starting_comment=False, count=1, message=fake.text(), visible=True
):
    comment_list = []
    for _ in range(count):
        message = message if message else fake.text()
        comment_list.append(
            Comment(
                message=message,
                marked_message=message,
                user=user,
                category=thread.category,
                thread=thread,
                is_starting_comment=is_starting_comment,
                visible=visible,
                created=timezone.now(),
                modified=timezone.now()
            )
        )
    Comment.objects.bulk_create(comment_list)
    return Comment.objects.last()
