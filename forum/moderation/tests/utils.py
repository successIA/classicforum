from ..models import Moderator


def make_moderator(user, category):
    mod = Moderator.objects.create(user=user)
    mod.categories.add(category)
    return mod