from django import template
from django.utils.text import Truncator

register = template.Library()


@register.simple_tag
def make_item_title(item, chars=32):
    tail = (
        ""
        if len(item.description) == 0
        else " (" + Truncator(item.description).chars(chars) + ")"
    )
    return type(item)._meta.verbose_name + " #" + str(item.pk) + tail
