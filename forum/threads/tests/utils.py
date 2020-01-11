from django.utils import timezone

from faker import Faker

fake = Faker()


def make_threads(
    count=1, user=None, category=None, 
    title=None, message=None, visible=True
):
    from forum.accounts.models import User
    from forum.categories.models import Category
    from forum.threads.models import Thread
    from forum.comments.models import Comment

    if not user:
        user = User.objects.create_user(username=Faker().name())
    if not category:
        category = Category.objects.create(
            title=Faker().sentence()[:50], description=Faker().texts()
        )

    threads = []
    for i in range(count):
        title = title if title else Faker().sentence()
        message = message if message else Faker().text()
        thread = Thread.objects.create(
            title=title,
            body="NA",
            user=user,
            category=category,
            visible=visible,
            created=timezone.now(),
            modified=timezone.now()
        )
        comment = Comment.objects.create(
            message=message,
            marked_message=message,
            user=user,
            category=thread.category,
            thread=thread,
            is_starting_comment=True,
            created=timezone.now(),
            modified=timezone.now())
        Thread.objects.filter(
            pk=thread.pk
        ).update(starting_comment=comment)
        thread.refresh_from_db()
        threads.append(thread)
    if count == 1:
        return threads[0]
    return threads


def make_only_thread(user, category, count=1, visible=True):
    from forum.threads.models import Thread
    if count > 1:
        thread_list = []
        for _ in range(count):
            thread_list.append(
                Thread(
                    title=fake.sentence(),
                    body="NA",
                    user=user,
                    category=category,
                    visible=visible,
                    created=timezone.now(),
                    modified=timezone.now()
                )
            )
        Thread.objects.bulk_create(thread_list)
    else:
        return Thread.objects.create(
            title=fake.sentence(),
            body="NA",
            user=user,
            category=category,
            visible=visible,
            created=timezone.now(),
            modified=timezone.now()
        )
