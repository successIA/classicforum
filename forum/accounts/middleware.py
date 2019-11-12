from django.utils import timezone

from forum.accounts.models import User
from forum.notifications.models import Notification


class UserLastSeenMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user and request.user.is_authenticated:
            User.objects.filter(pk=request.user.pk).update(
                last_seen=timezone.now()
            )
            notif_url, notif_count = Notification.objects.get_receiver_url_and_count(
                request.user
            )
            request.user.notif_url = notif_url
            request.user.notif_count = notif_count
        return self.get_response(request)
