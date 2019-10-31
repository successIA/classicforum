from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.http import HttpResponseRedirect

from forum.attachments.forms import AttachmentForm
from forum.attachments.models import Attachment



@login_required
def upload(request):
    from hashlib import md5
    if request.method == "POST":
        data = {}
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            if request.is_ajax():
                instance = form.save(commit=False)
                instance.filename = instance.image.name
                md5 = md5()
                for chunk in instance.image.chunks():
                    md5.update(chunk)
                md5sum = md5.hexdigest()
                attachment_qs = Attachment.objects.filter(md5sum=md5sum)
                if attachment_qs.exists():
                    instance = attachment_qs.first()
                else:
                    instance.save()
                data = {
                    'is_valid': True,
                    'name': instance.image.name,
                    'url': instance.image.url
                }
        else:
            data = {
                    'is_valid': False,
                    'message': form.errors['image'][0]
                }
        return JsonResponse(data)
                
    url = '/' + '?#down'
    return HttpResponseRedirect(url)
