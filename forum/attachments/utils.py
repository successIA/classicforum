import re
from markdown import markdown

from django.utils.html import mark_safe

from forum.attachments.models import Attachment


def associate_attachment_with_comment(new_comment, old_comment=None):
    if old_comment:
        detach_comment_from_attachment(new_comment, old_comment)
    add_comment_to_attachment(new_comment)


def add_comment_to_attachment(comment):
    image_url_list = find_images_in_message(comment.message)
    print('comment', comment)
    print('image_url_list', image_url_list)
    for url in image_url_list:
        url = url.replace('http://127.0.0.1:8000', "")
        print('url', url)
        if url:
            attachment_qs = Attachment.objects.filter(url=url)
        if attachment_qs.exists():
            attachment = attachment_qs.first()
            print('attachment', attachment)
            attachment.comments.add(comment)
            attachment.is_orphaned = False
            attachment.save()



def detach_comment_from_attachment(new_comment, old_comment):
    '''
    Detach comment from all its attachments if there is any
    change in the image urls in the message
    '''
    old_list = find_images_in_message(old_comment.message)
    new_list = find_images_in_message(new_comment.message)
    black_list = [url for url in old_list if url not in new_list]
    if not black_list:
        return
    black_list = strip_ip_from_url(black_list)
    att_qs_obj = comment.attachment_set
    if not att_qs_obj.exists():
        return
    for att in att_qs_obj.all():
        if att.url in black_list:
            att.comments.remove(comment)
            if not att.userprofile and att.comments.all().count() < 1\
                and att.threads.all().count() < 1:
                att.is_orphaned = True
                att.save()    

def strip_ip_from_url(url_list):
    return [url.replace('http://127.0.0.1:8000', "") for url in url_list]

def find_images_in_message(message):
    img_regex = r'<img(?:.+?)src="(?P<src>.+?)"(?:.*?)>'
    message = mark_safe(markdown(message, safe_mode='escape'))
    return re.findall(img_regex, message)

def create_attachment_by_profile(image, userprofile):
    if not image:
        return
    md5sum = md5(image)
    attachment_qs = Attachment.objects.filter(md5sum=md5sum)
    if attachment_qs.exists():
        attachment_qs.first().userprofiles.add(userprofile)
    else:
        att = Attachment(image=image, filename=image.name, has_userprofile=True)
        att.save()
        att.userprofiles.add(userprofile)

def md5(file=None):
    from hashlib import md5

    if not file:
        return None
    md5 = md5()
    for chunk in file.chunks():
        md5.update(chunk)
    return md5.hexdigest()

# def add_instance_to_attachment(instance, url_list):
#     for url in url_list:
#         url = url.replace('http://127.0.0.1:8000', "")
#         if url:
#             attachment_qs = Attachment.objects.filter(url=url)
#         if attachment_qs.exists():
#             attachment = attachment_qs.first()
#             attachment.comments.add(instance)
#             attachment.is_orphaned = False
#             attachment.save()

# def detach_instance_from_attachment(comment, url_list):
#     if not url_list:
#         return
#     url_list = strip_ip_from_url(url_list)
#     att_qs_obj = comment.attachment_set
#     if not att_qs_obj.exists():
#         return
#     for att in att_qs_obj.all():
#         if att.url in url_list:
#             att.comments.remove(comment)
#             if not att.userprofile \
#                 and att.comments.all().count() < 1 \
#                 and att.threads.all().count() < 1:
#                 att.is_orphaned = True
#                 att.save()
