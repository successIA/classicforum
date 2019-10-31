from django.utils import timezone

from forum.accounts.models import UserProfile


class UserLastSeenMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user and request.user.is_authenticated:
            UserProfile.objects.filter(user=request.user).update(
                last_seen=timezone.now()
            )
        return self.get_response(request)