# halls/templatetags/__init__.py  ← ملف فارغ لازم يكون موجود
# halls/templatetags/hall_extras.py

from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, [])

@register.filter
def color_index(value, count=6):
    return value % count
