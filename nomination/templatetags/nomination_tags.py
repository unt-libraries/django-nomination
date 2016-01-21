from django import template
from django.template.defaultfilters import stringfilter


register = template.Library()

@register.filter
@stringfilter
def replaceunderscores(value):
    return value.replace('_',' ')

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
