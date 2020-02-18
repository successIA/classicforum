from django.db.models import Max, Min, Count, F, Value, CharField, Prefetch
from django.db import models
from django.shortcuts import get_object_or_404


class CommentQuerySet(models.query.QuerySet):
    def get_new_for_user(self, user, thread, time):
        if not user.is_authenticated:
            return
        if not time:
            return
        queryset = self.filter(thread=thread, created__gt=time)
        return queryset.exclude(user=user)

    def get_for_thread(self, thread):
        queryset = self.active().get_related().filter(
            thread=thread
        ).exclude(is_starting_comment=True)
        return queryset.order_by('created').all()

    def get_user_last_posted(self, user):
        queryset = list(self.filter(user=user).all())
        if len(queryset) > 0:
            return queryset[-1].created

    def get_user_active_category(self, user, comment_count):
        if comment_count > 0:
            return self.values('thread').filter(
                user=user
            ).annotate(category=F('thread__category__title')).annotate(
                thread_count=Count('thread')
            ).order_by('-thread_count')[0].get('category')

    def get_recent_for_user(self, user, count):
        return self.get_related().filter(
            user=user
        ).exclude(is_starting_comment=True).order_by('-created')[:count]

    def get_user_total_upvotes(self, user):
        queryset = self.filter(user=user).annotate(upvotes=Count('upvoters'))
        total_upvotes = 0
        for model_instance in queryset:
            total_upvotes = total_upvotes + model_instance.upvotes
        return total_upvotes

    def get_related(self):
        return self.select_related(
            'thread', 'user', 'parent'
        ).prefetch_related(
            'user__followers',
            'revisions',
            'parent__user',
            'parent__thread',
            'upvoters',
            'downvoters'
        )

    def get_parent(self, pk):
        comment_qs = None
        try:
            comment_qs = self.filter(pk=int(pk))
        except:
            return None
        if comment_qs:
            return comment_qs[0]

    def pure(self):
        return self.filter(is_starting_comment=False)

    def pure_and_active(self):
        return self.active().pure()
    
    def pure_and_active_or_404(self, pk):
        return get_object_or_404(
            self.model, visible=True, is_starting_comment=False, pk=pk
        )
    
    def pure_and_thread_active_or_404(self, pk):
        return get_object_or_404(
            self.model, 
            thread__visible=True,
            visible=True, 
            is_starting_comment=False, 
            pk=pk
        )
    
    def active(self, *args, **kwargs):
        return self.filter(visible=True)
