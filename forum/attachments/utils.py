import re

from django.utils.html import mark_safe

from markdown import markdown


def get_unreferenced_image_srcs_in_message(prev_message, message):
    prev_msg_img_url_list = find_images_in_message(prev_message)
    msg_img_url_list = find_images_in_message(message)
    return [url for url in prev_msg_img_url_list if url not in msg_img_url_list]


def find_images_in_message(message):
    img_regex = r'<img(?:.+?)src="(?P<src>.+?)"(?:.*?)>'
    message = mark_safe(markdown(message, safe_mode='escape'))
    return re.findall(img_regex, message)


def md5(file=None):
    from hashlib import md5

    if not file:
        return None
    md5 = md5()
    for chunk in file.chunks():
        md5.update(chunk)
    return md5.hexdigest()
