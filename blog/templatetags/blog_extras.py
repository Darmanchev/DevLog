import math
import re

import markdown
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

READING_WORDS_PER_MINUTE = 200

@register.filter(name='markdown')
def markdown_format(text):
    if not text:
        return ""
    md = markdown.Markdown(extensions=['fenced_code', 'tables', 'nl2br'])
    return mark_safe(md.convert(escape(text)))

@register.filter(name='read_time')
def read_time(text):
    if not text:
        return 1
    word_count = len(re.findall(r'\w+', text, flags=re.UNICODE))
    return max(1, math.ceil(word_count / READING_WORDS_PER_MINUTE))
