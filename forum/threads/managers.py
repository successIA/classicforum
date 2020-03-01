from datetime import timedelta

from django.db import models
from django.db.models import CharField, Count, F, Max, Min, Prefetch, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.text import slugify

from forum.core.utils import get_random_string


class ThreadQuerySet(models.query.QuerySet):
    def generate_slug(self, instance, new_slug=None):
        slug = None
        if new_slug:
            slug = new_slug
        elif instance.slug:
            slug = slugify(instance.slug)
        else:
            slug = slugify(instance.title)
        qs = self.filter(slug=slug)
        if qs.exists():
            new_slug = '%s-%s' % (slug, get_random_string())
            return self.generate_slug(instance, new_slug=new_slug)
        return slug

    def get_all(self, cat_slug=None):
        if cat_slug:
            qs = self.filter(category__slug=cat_slug)
            if qs:
                return qs, qs.first().category
        return self, False

    def get_for_user(self, request):
        queryset = self

        if not request.user.is_authenticated:
            return queryset.get_related()
            
        queryset1 = queryset.get_related().filter(
            followers=request.user
        ).annotate(
            new_c_id=F('threadfollowership__first_new_comment'),
            new_c_num=F('threadfollowership__new_comment_count')
        )
    
        queryset2 = queryset.get_related().exclude(
            followers=request.user
        ).annotate(
            new_c_id=Value('0', output_field=CharField()),
            new_c_num=Value('0', output_field=CharField())
        )
        return queryset1.union(queryset2)

    def get_recent(self, request):
        return self.get_for_user(
            request
        ).order_by('-final_comment_time')
        
    def get_new_for_user(self, request):
        queryset = self
        if not request.user.is_authenticated:
            return queryset.get_related()
        queryset = queryset.get_related().filter(
            followers=request.user, 
            threadfollowership__new_comment_count__gt=0
        ).annotate(
            new_c_id=F('threadfollowership__first_new_comment'),
            new_c_num=F('threadfollowership__new_comment_count')
        ).order_by('threadfollowership__first_new_comment__created')
        return queryset

    def get_following_for_user(self, request):
        queryset = self
        if not request.user.is_authenticated:
            return queryset.get_related()
        queryset = queryset.get_related().filter(
            followers=request.user
        ).annotate(
            new_c_id=F('threadfollowership__first_new_comment'),
            new_c_num=F('threadfollowership__new_comment_count')
        )
        return queryset.order_by('-comment_count')

    def get_only_for_user(self, request):
        queryset = self
        if not request.user.is_authenticated:
            return queryset.get_related()
        queryset1 = queryset.get_related().filter(
            user=request.user, threadfollowership__user=request.user
        ).annotate(
            new_c_id=F('threadfollowership__first_new_comment'),
            new_c_num=F('threadfollowership__new_comment_count')
        )
        queryset2 = queryset.get_related().filter(
            user=request.user
        ).exclude(
            threadfollowership__user=request.user
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
                request
            ).order_by('-final_comment_time')[:count]
        return self.get_related().filter(
            user=user
        ).order_by('-final_comment_time')[:count]

    def get_with_no_reply(self, category=None):
        queryset = self
        queryset = queryset.filter(comment_count=0).get_related()
        if not category:
            return queryset.order_by('-created')
        queryset = queryset.filter(category=category).order_by('-created')
        return queryset

    def get_by_days_from_now(self, request, days=None):
        queryset = self
        if days:
            dt = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(created__gte=dt)
        return queryset.get_for_user(request).order_by('-comment_count')

    def get_by_category(self, category=None):
        if not category:
            return self.get_related()
        return self.filter(category=category).get_related()

    def get_related(self):
        return self.select_related(
            'user', 'category', 'final_comment_user', 'starting_comment'
        ).prefetch_related(
            'hit_counts'
        )

    def active(self, visible=True):
        return self.filter(visible=True)
