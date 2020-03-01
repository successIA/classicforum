import re
from math import ceil
from timeit import default_timer as timer

from django.db.models import F

from markdown import markdown

from forum.core.constants import COMMENT_PER_PAGE


class BBCodeQuoteWithMarkdownParser:
    def __init__(self, text):
        self.text = text
        self.open_tag_capture_regex = r'\[quote(\s*)?=(\s*")?(?P<username>[^\]\n]*?)(\s*,\s*)?([A-Za-z]+?)?(\s*:\s*)?(?P<id>\d+)?(\s*"\s*)?\]'
        self.open_and_close_tag_regex = r'((\[quote(?![A-Za-z\n])(?:[^\]]*?)?\])(?![\s\S]*?\[quote(?![A-Za-z\n])(?:[^\]]*?)?\][\s\S]*?\[/quote\])([\s\S]*?)(\[/quote\]))'
        self.comment_pk_set = set()
        self.text_comment_qs = list()

    def _get_markdown_ext(self, text):
        return markdown(text, extensions=['prependnewline'])
    
    def _replace_three_newlines_with_two(self, text):
        three_line_break_chars = r'([\r|\n]){3,}'
        return re.sub(three_line_break_chars, "\n\n", text)
                        
    def parse(self):
        self._gather_comment_pk_from_text(self.text)
        self.text_comment_qs = self._get_comment_queryset()
        text = self._render_quotes_as_html(self.text)
        text = self._replace_three_newlines_with_two(text)
        text = self._get_markdown_ext(text)
        return text
    
    def _add_to_comment_pk_set(self, match):
        result = re.search(
            self.open_tag_capture_regex, match.group(2), re.DOTALL
        )
        if result and result.groupdict():
            username = result.groupdict().get('username').strip()
            comment_id_str = result.groupdict().get('id').strip()
            try:
                if username and comment_id_str:
                    comment_id = int(comment_id_str)
                    self.comment_pk_set.add(comment_id)
                    return 'match_success'
            except ValueError:
                pass
        return 'match_failed'

    def _gather_comment_pk_from_text(self, text):
        replaced_text, num_of_matches = re.subn(
            self.open_and_close_tag_regex, 
            self._add_to_comment_pk_set, 
            text
        )
        if num_of_matches > 0:
            return self._gather_comment_pk_from_text(replaced_text)
        
    def _get_comment_queryset(self):
        if self.comment_pk_set:
            from forum.comments.models import Comment
            return Comment.objects.filter(
                pk__in=self.comment_pk_set
            ).annotate(username=F('user__username'))
        else:
            return list()
    
    def _get_comment_from_text_comment_qs(self, comment_pk, username):
        if comment_pk and username:
            for comment in self.text_comment_qs:
                if comment.pk == comment_pk and comment.username == username:
                    return comment
        return None

    def _replace_with_blockquote(self, match):
        marked_text = self._get_markdown_ext(match.group(3).strip())
        result = re.search(
            self.open_tag_capture_regex, match.group(2), re.DOTALL
        )
        if result and result.groupdict():
            username = result.groupdict().get('username').strip()
            comment_id_str = result.groupdict().get('id').strip()
            try:
                comment = self._get_comment_from_text_comment_qs(int(comment_id_str), username)
                if comment:
                    return f'<aside class="quote"><blockquote><div class="title"><a href="{comment.get_precise_url()}">{username}</a> said:</div>{marked_text}</blockquote></aside>'
            except ValueError:
                pass        
        return f'<aside class="quote"><blockquote>{marked_text}</blockquote></aside>'

    def _render_quotes_as_html(self, text):
        replaced_text, num_of_matches = re.subn(
            self.open_and_close_tag_regex, self._replace_with_blockquote, text
        )
        if num_of_matches > 0:
            return self._render_quotes_as_html(replaced_text)
        else:
            return replaced_text
