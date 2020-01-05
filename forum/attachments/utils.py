import re

# from django.utils.html import mark_safe

from markdown import markdown


def get_unref_image_srcs_in_msg(prev_msg, curr_msg):
    prev_src_set = set(get_image_srcs_from_msg(prev_msg))
    curr_src_set = set(get_image_srcs_from_msg(curr_msg))
    return prev_src_set.difference(curr_src_set)


def get_image_srcs_from_msg(message):
    img_regex = r'<img(?:.+?)src="(?P<src>.+?)"(?:.*?)>'
    message = markdown(message)
    return re.findall(img_regex, message)


def md5(file=None):
    from hashlib import md5

    if file:
        md5 = md5()
        for chunk in file.chunks():
            md5.update(chunk)
        return md5.hexdigest()
