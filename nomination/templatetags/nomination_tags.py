from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

import markdown


register = template.Library()


@register.filter
@stringfilter
def replaceunderscores(value):
    return value.replace('_', ' ')


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
@stringfilter
def render_markdown(value):
    return mark_safe(markdown.markdown(value, output_format='html5'))
