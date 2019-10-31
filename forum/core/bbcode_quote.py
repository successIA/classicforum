import re
from math import ceil

from forum.core.constants import COMMENT_PER_PAGE

# Match [quote  only if charater A-Za-z and newline character does not follow
# Match as many characters except ] (closing square bracket) if present
# Match ] and as many whitespace character if present and a compulsory new line character
quote_start_tag_regex = r'(\[quote)(?![A-Za-z\n])([^\]]*?)?(\])[\s]*?[\n]'
quote_placeholder_start_tag_regex = r'\[quote(\s*)?=(\s*")?(?P<username>[^\]\n]*?)(\s*,\s*)?([A-Za-z]+?)?(\s*:\s*)?(?P<id>\d+)?(\s*"\s*)?\][\s]*?[\n]'
# quote_placeholder_start_tag_regex = '\[quote(\s*)?=(\s*")?(?P<username>[^\]\n]*?)(\s*,\s*)?(\w+?)?(\s*:\s*)?(?P<id>\d+)?(\s*"\s*)?\][\s]*?[\n]'

quote_end_tag_regex = r'\[/quote\][\s]*?[\n]'
quote_syntax_regex = r'((\[quote(?![A-Za-z\n])(?:[^\]]*?)?\][\s]*?[\n])(?![\s\S]*?\[quote(?![A-Za-z\n])(?:[^\]]*?)?\][\s]*?[\n][\s\S]*?\[/quote\][\s]*?[\n])([\s\S]*?)(\[/quote\][\s]*?[\n]))'

comment_info_list = []
def replace(match):   
    result = re.search(quote_placeholder_start_tag_regex, match.group(2), re.DOTALL).groupdict()
    if result and result.get('username') and result.get('id'):
        comment_info_list.append(result)
        username = result.get('username').strip()
        comment_id = result.get('id').strip()
        comment = None
        try:
            from forum.comments.models import Comment        
            comment_qs = Comment.objects.filter(
                pk=int(comment_id),
                user__username=username
            )
            page_num = 0
            if comment_qs.exists():
                comment = comment_qs.first()
                count = comment_qs.first().position
                page_num = ceil(count / COMMENT_PER_PAGE) 
        except:
            pass
        finally:
            thread_absolute_url = ''
            if comment:
                blockquote = '<aside class="quote"><blockquote>'\
                    +  '<div class="title"><a href="' + comment.get_precise_url(page_num) + '"#comment' + str(comment.id) + '">'\
                     + username + '</a> said:</div>' + match.group(3).strip() \
                        + '</blockquote></aside>'
            else:
                blockquote = '<aside class="quote"><blockquote>' + '<p>' + \
                                    match.group(3).strip() + '</p>' + '</blockquote></aside>'
            return blockquote
    elif (start_tag_test and end_tag_test):
        blockquote = '<aside class="quote"><blockquote>' + '<p>' + \
            match.group(3).strip() + '</p>' + '</blockquote></aside>'
        return blockquote
    else:
        html = match.group(2) + match.group(3) + match.group(4)
        return html

def bbcode_quote(text):
    placeholder_start_tag_count = len(re.findall(quote_placeholder_start_tag_regex, text))
    start_tag_count = len(re.findall(quote_start_tag_regex, text))
    end_tag_count = len(re.findall(quote_end_tag_regex, text))
    start_tag_total_count = placeholder_start_tag_count + start_tag_count
    tag_length = start_tag_total_count if (start_tag_total_count <= end_tag_count) else end_tag_count
    for count in range(tag_length):        
        placeholder_start_tag_test = len(re.findall(quote_placeholder_start_tag_regex, text)) > 0
        start_tag_test = len(re.findall(quote_start_tag_regex, text)) > 0
        end_tag_test = len(re.findall(quote_end_tag_regex, text)) > 0
        if (placeholder_start_tag_test and end_tag_test) or (start_tag_test and end_tag_test):
            text = re.sub(quote_syntax_regex, replace, text)
        else:
            break
    three_line_break_chars = r'([\r|\n)]){3,}';
    text = re.sub(three_line_break_chars, "\n\n", text);
    return text, comment_info_list