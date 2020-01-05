from django.utils import timezone

from faker import Faker

from forum.comments.models import Comment

fake = Faker()


def make_comment(
    user, thread, is_starting_comment=False, count=1, message=fake.text()
):
    comment_list = []
    for _ in range(count):
        comment_list.append(
            Comment(
                message=message if count == 1 else fake.text(),
                user=user,
                category=thread.category,
                thread=thread,
                is_starting_comment=is_starting_comment,
                created=timezone.now(),
                modified=timezone.now()
            )
        )
    # Use bulk_create instead of save to that not to
    # hit the overriden model save method.
    Comment.objects.bulk_create(comment_list)
    return Comment.objects.last()


# def assert_not_added_to_db(function):
#     from forum.comments.forms import Comment

#     def wrap(test_case, *args, **kwargs):
#         test_case.assertEquals(Comment.objects.all().count(), 1)
#         return function(test_case, *args, **kwargs)
#         test_case.assertEquals(Comment.objects.all().count(), 1)
#     wrap.__doc__ = function.__doc__
#     wrap.__name__ = function.__name__
#     return wrap
