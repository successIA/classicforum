from datetime import timedelta

from django.db import models
from django.db.models import Max, Min, Count, F, Value, CharField, Prefetch
from django.utils import timezone


class ThreadQuerySet(models.query.QuerySet):

    # def get_new_for_user2(self, user):
    #     return self.get_related().filter(
    #         reader=user, followers=user
    #     ).annotate(
    #         new_c_id=F('thread_activity__comment')
    #         new_c_num=Count('thread_activity__comment')
    #     )

    # def get_all2(self, user):
    #     qs1 = self.get_for_user2(user)
    #     qs2 = queryset.get_related().exclude(
    #         followers=user
    #     ).annotate(
    #         new_c_id=Value('0', output_field=CharField()),
    #         new_c_num=Value('0', output_field=CharField())
    #     )
    #     return qs1.union(qs2)

    def get_all(self, cat_slug=None):
        if cat_slug:
            qs = self.active().filter(category__slug=cat_slug)
            if qs:
                return qs, qs.first().category
        return self.active(), False

    def get_for_user(self, user):
        queryset = self
        if not user.is_authenticated:
            return queryset.get_related()
        queryset1 = queryset.get_related().filter(
            followers=user
        ).annotate(
            new_c_id=F('threadfollowership__final_comment'),
            new_c_num=F('threadfollowership__new_comment_count')
        )
        queryset2 = queryset.get_related().exclude(
            followers=user
        ).annotate(
            new_c_id=Value('0', output_field=CharField()),
            new_c_num=Value('0', output_field=CharField())
        )
        return queryset1.union(queryset2)

    def get_recent(self, user):
        return self.get_for_user(user).order_by('-final_comment_time')

    def get_new_for_user(self, user):
        queryset = self
        if not user.is_authenticated:
            return queryset.get_related()
        queryset = queryset.get_related().filter(
            followers=user, threadfollowership__has_new_comment=True
        ).annotate(
            new_c_id=F('threadfollowership__final_comment'),
            new_c_num=F('threadfollowership__new_comment_count')
        ).order_by('threadfollowership__final_comment__created')
        return queryset

    def get_following_for_user(self, user):
        queryset = self
        if not user.is_authenticated:
            return queryset.get_related()
        queryset = queryset.get_related().filter(
            followers=user
        ).annotate(
            new_c_id=F('threadfollowership__final_comment'),
            new_c_num=F('threadfollowership__new_comment_count')
        )
        return queryset.order_by('-comment_count')

    def get_only_for_user(self, user):
        queryset = self
        if not user.is_authenticated:
            return queryset.get_related()
        queryset1 = queryset.get_related().filter(
            user=user, threadfollowership__user=user
        ).annotate(
            new_c_id=F('threadfollowership__final_comment'),
            new_c_num=F('threadfollowership__new_comment_count')
        )
        queryset2 = queryset.get_related().filter(
            user=user
        ).exclude(
            threadfollowership__user=user
        ).annotate(
            new_c_id=Value('0', output_field=CharField()),
            new_c_num=Value('0', output_field=CharField())
        )
        queryset = queryset1.union(queryset2)
        return queryset.order_by('-comment_count')

    def get_recent_for_user(self, request, user, count=5):
        is_auth = request.user.is_authenticated
        if is_auth and request.user.is_owner(user):
            return self.get_only_for_user(
                user
            ).order_by('-final_comment_time')[:count]
        return self.active().get_related().filter(
            user=user
        ).order_by('-final_comment_time')[:count]

    def get_with_no_reply(self, category=None):
        queryset = self
        queryset = queryset.filter(comment_count=1).get_related()
        if not category:
            return queryset.order_by('-created')
        queryset = queryset.filter(category=category).order_by('-created')
        return queryset

    def get_by_days_from_now(self, user, days=None):
        queryset = self
        if days:
            dt = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(created__gte=dt)
        return queryset.get_for_user(user).order_by('comment_count')

    def get_by_category(self, category=None):
        if not category:
            return self.active().get_related()
        return self.active().filter(category=category).get_related()

    def get_related(self):
        return self.select_related(
            'user', 'category', 'final_comment_user', 'starting_comment'
        ).prefetch_related(
            'final_comment_user'
        )

    def active(self, *args, **kwargs):
        return self.filter(visible=True)
