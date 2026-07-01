from html import unescape

import bleach
import markdown
from django.utils.html import strip_tags


MARKDOWN_EXTENSIONS = ['fenced_code', 'tables', 'nl2br']
ALLOWED_TAGS = {
    'a',
    'blockquote',
    'br',
    'code',
    'em',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'li',
    'ol',
    'p',
    'pre',
    'strong',
    'table',
    'tbody',
    'td',
    'th',
    'thead',
    'tr',
    'ul',
}
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'code': ['class'],
}
ALLOWED_PROTOCOLS = {'http', 'https', 'mailto'}


def render_markdown_html(text):
    if not text:
        return ''

    html = markdown.markdown(str(text), extensions=MARKDOWN_EXTENSIONS)
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
    )


def render_markdown_plain_text(text):
    return unescape(strip_tags(render_markdown_html(text)))
