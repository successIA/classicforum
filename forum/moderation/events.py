from ..categories.models import Category
from .models import ModeratorEvent


def create_moderator_added_event(user, categories):
    event = ModeratorEvent.objects.create(
        event_type=ModeratorEvent.MODERATOR_ADDED, user=user
    )
    event.categories.add(*categories) 

def create_moderator_removed_event(user, categories):
    event = ModeratorEvent.objects.create(
        event_type=ModeratorEvent.MODERATOR_REMOVED, user=user
    )
    event.categories.add(*categories) 

def create_category_changed_event(user, prev_cats, curr_cats):
    prev_cat_pks = {c.pk for c in prev_cats}
    curr_cat_pks = {c.pk for c in curr_cats}
    detached_cats, fresh_cats = Category.objects.get_difference(
        prev_cat_pks, curr_cat_pks
    )

    if fresh_cats:
        event = ModeratorEvent.objects.create(
            user=user,
            event_type=ModeratorEvent.CATEGORY_ADDED
        )
        event.categories.add(*fresh_cats)

    if detached_cats:
        event = ModeratorEvent.objects.create(
            user=user,
            event_type=ModeratorEvent.CATEGORY_REMOVED
        )
        event.categories.add(*detached_cats)
