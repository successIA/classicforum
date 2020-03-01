from django.db import models
from django.db.models import CharField, Count, F, Max, Min, Prefetch, Value
from django.shortcuts import get_object_or_404


class CommentQuerySet(models.query.QuerySet):
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
        
    def get_user_total_likes(self, user):
        queryset = self.filter(user=user).annotate(likes=Count('likers'))
        total_likes = 0
        for model_instance in queryset:
            total_likes = total_likes + model_instance.likes
        return total_likes

    def get_related(self):
        return self.select_related(
            'thread', 'user', 'parent'
        ).prefetch_related(
            'user__followers',
            'revisions',
            'parent__user',
            'parent__thread',
            'likers',
        )

    def get_parent(self, pk):
        comment_qs = None
        try:
            comment_qs = self.filter(pk=int(pk))
        except:
            return None
        if comment_qs:
            return comment_qs[0]

    def get_pure_and_thread_active_for_user(self, user):
        return self.filter(
            user=user,
            thread__visible=True,
        ).pure_and_active().get_related().order_by('-id')

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

    def pure(self):
        return self.filter(is_starting_comment=False)
    
    def active(self, *args, **kwargs):
        return self.filter(visible=True)
