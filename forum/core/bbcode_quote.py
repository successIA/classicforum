import re
from math import ceil
from timeit import default_timer as timer

from markdown import markdown

from forum.core.constants import COMMENT_PER_PAGE

# Match [quote  only if charater A-Za-z and newline character does not follow
# Match as many characters except ] (closing square bracket) if present
# Match ] and as many whitespace character if present and a compulsory new line character
# open_tag_regex = r'(\[quote)(?![A-Za-z\n])([^\]]*?)?(\])[\s]*?[\n]'

open_tag_regex = r'(\[quote)(?![A-Za-z\n])([^\]]*?)?(\])'

open_tag_capture_regex = r'\[quote(\s*)?=(\s*")?(?P<username>[^\]\n]*?)(\s*,\s*)?([A-Za-z]+?)?(\s*:\s*)?(?P<id>\d+)?(\s*"\s*)?\]'
# open_tag_capture_regex = r'\[quote(\s*)?=(\s*")?(?P<username>[^\]\n]*?)(\s*,\s*)?([A-Za-z]+?)?(\s*:\s*)?(?P<id>\d+)?(\s*"\s*)?\][\s]*?[\n]'
# open_tag_capture_regex = '\[quote(\s*)?=(\s*")?(?P<username>[^\]\n]*?)(\s*,\s*)?(\w+?)?(\s*:\s*)?(?P<id>\d+)?(\s*"\s*)?\][\s]*?[\n]'

# close_tag_regex = r'\[/quote\][\s]*?[\n]'
close_tag_regex = r'\[/quote\]'

# open_and_close_tag_regex = r'((\[quote(?![A-Za-z\n])(?:[^\]]*?)?\][\s]*?[\n])(?![\s\S]*?\[quote(?![A-Za-z\n])(?:[^\]]*?)?\][\s]*?[\n][\s\S]*?\[/quote\][\s]*?[\n])([\s\S]*?)(\[/quote\][\s]*?[\n]))'
open_and_close_tag_regex = r'((\[quote(?![A-Za-z\n])(?:[^\]]*?)?\])(?![\s\S]*?\[quote(?![A-Za-z\n])(?:[^\]]*?)?\][\s\S]*?\[/quote\])([\s\S]*?)(\[/quote\]))'

comment_info_list = []

def markdown_ext(text):
    return markdown(text, extensions=['prependnewline'])


def get_parent_comment_info(comment_info_dict):
    comment = None
    username = comment_info_dict.get('username').strip()
    comment_id_str = comment_info_dict.get('id').strip()
    try:
        comment_id = int(comment_id_str)
        if username and comment_id:        
            from forum.comments.models import Comment
            # comment_info_list.append(comment_info_dict)
            comment_list = list(Comment.objects.filter(
                pk=comment_id, user__username=username
            ))
            comment = comment_list[0] if comment_list else None
    except ValueError:
        pass
    return comment, username
       
            
def replace(match):
    marked_text = markdown_ext(match.group(3).strip())
    result = re.search(
        open_tag_capture_regex, match.group(2), re.DOTALL
    )
    if result and result.groupdict():
        comment, username = get_parent_comment_info(result.groupdict())
        if comment and username:
            return f'<aside class="quote"><blockquote><div class="title"><a href="{comment.get_precise_url()}">{username}</a> said:</div>{marked_text}</blockquote></aside>'
        else:
            return f'<aside class="quote"><blockquote>{marked_text}</blockquote></aside>'

    elif len(re.findall(open_tag_regex, match.group(2))) > 0:
        return f'<aside class="quote"><blockquote>{marked_text}</blockquote></aside>'
    else:
        html = markdown(match.group(2)) + marked_text + markdown(match.group(4))
        return html


def bbcode_quote(text):
    t0 = timer()

    placeholder_start_tag_count = len(re.findall(
        open_tag_capture_regex, text)
    )
    start_tag_count = len(re.findall(open_tag_regex, text))
    end_tag_count = len(re.findall(close_tag_regex, text))
    start_tag_total_count = placeholder_start_tag_count + start_tag_count

    tag_length = start_tag_total_count if (
        start_tag_total_count <= end_tag_count
    ) else end_tag_count

    found_any_match = False
    for count in range(tag_length):
        placeholder_start_tag_test = len(re.findall(
            open_tag_capture_regex, text)
        ) > 0

        start_tag_test = len(re.findall(open_tag_regex, text)) > 0
        end_tag_test = len(re.findall(close_tag_regex, text)) > 0

        if (placeholder_start_tag_test and end_tag_test) or (start_tag_test and end_tag_test):
            found_any_match = True
            text = re.sub(open_and_close_tag_regex, replace, text)
        else:
            break
    # three_line_break_chars = r'([\r|\n)]){3,}'
    three_line_break_chars = r'([\r|\n]){3,}'

    text = re.sub(three_line_break_chars, "\n\n", text)
    if not found_any_match:
        text = markdown_ext(text)
    
    t1 = timer()
    print('Time:', t1 - t0)
    return text, comment_info_list
