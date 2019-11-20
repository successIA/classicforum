from django.urls import reverse


def make_category(title="progromming group", description="NA"):
    from forum.categories.models import Category

    return Category.objects.create(
        title=title,
        description=description
    )
