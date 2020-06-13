from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, Http404

from forum.attachments.forms import AttachmentForm
from forum.attachments.mixins import ajax_required
from forum.attachments.models import Attachment
from forum.attachments.utils import md5
from forum.core.utils import strip_leading_slash


@login_required
@ajax_required
def upload(request):
    if not settings.DEBUG:
        raise Http404
    if request.method == "POST":
        data = {}
        form = AttachmentForm(request.POST, request.FILES)

        if form.is_valid():       
            attachment = form.save(commit=False)            
            md5sum = md5(attachment.image)
            attachment_qs = Attachment.objects.filter(
                md5sum=md5sum, is_avatar=False
            )
            
            if attachment_qs:
                attachment = attachment_qs[0]
            else:
                attachment.md5sum = md5sum
                attachment.save()
            data = {
                'is_valid': True,
                'name': attachment.image.name,
                'url': attachment.image.url
            }
        else:
            data = {
                'is_valid': False,
                'message': form.errors['image'][0]
            }
        return JsonResponse(data)
