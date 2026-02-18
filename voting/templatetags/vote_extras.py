from django import template

register = template.Library()

@register.filter(name='get_range')
def get_range(value):
    try:
        return range(1, value + 1)
    except (ValueError, TypeError):
        return []
