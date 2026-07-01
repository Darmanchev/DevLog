import math
import re

from django import template
from django.utils.safestring import mark_safe

from blog.markdown_utils import render_markdown_html, render_markdown_plain_text

register = template.Library()

READING_WORDS_PER_MINUTE = 200

@register.filter(name='markdown')
def markdown_format(text):
    return mark_safe(render_markdown_html(text))

@register.filter(name='markdown_plain')
def markdown_plain_text(text):
    return render_markdown_plain_text(text)

@register.filter(name='read_time')
def read_time(text):
    if not text:
        return 1
    word_count = len(re.findall(r'\w+', text, flags=re.UNICODE))
    return max(1, math.ceil(word_count / READING_WORDS_PER_MINUTE))
