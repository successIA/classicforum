from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import Http404
from django.shortcuts import get_object_or_404

from forum.threads.models import Thread


class ThreadOwnerMixin(object):

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        slug = kwargs.get('thread_slug')
        # thread = Thread.objects.get(slug=slug)
        thread = get_object_or_404(Thread, slug=slug)
        is_owner = thread.is_owner(request.user)
        kwargs['thread'] = thread
        if is_owner:
            return super(ThreadOwnerMixin, self).dispatch(request, *args, **kwargs)
        else:
            raise Http404


def thread_owner_required(function):
    def wrap(request, *args, **kwargs):
        thread = get_object_or_404(Thread, slug=kwargs.get('thread_slug'))
        if not thread.is_owner(request.user):
            raise PermissionDenied
        kwargs['thread'] = thread
        return function(request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap

