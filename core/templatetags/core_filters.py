# core/templatetags/core_filters.py

from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    """
    Adds a CSS class to a form field.
    Usage: {{ field|add_class:"my-class" }}
    """
    return value.as_widget(attrs={'class': arg})

@register.filter(name='add_placeholder')
def add_placeholder(field, text):
    """
    Adds a placeholder attribute to a form field.
    Usage: {{ field|add_placeholder:"Enter your username" }}
    """
    field.field.widget.attrs['placeholder'] = text
    return field

@register.filter(name='is_checkbox')
def is_checkbox(field):
    return field.field.widget.__class__.__name__ == 'CheckboxInput'

@register.filter
def startswith(value, arg):
    """
    Checks if a string starts with a given substring.
    Usage: {{ value|startswith:arg }}
    """
    return value.startswith(arg)

@register.filter
def replace(value, arg):
    """
    Replaces all occurrences of a substring with another.
    The argument format must be 'old,new'.
    Usage: {{ value|replace:"old,new" }}
    """
    if isinstance(arg, str) and ',' in arg:
        old, new = arg.split(',', 1)
        return value.replace(old, new)
    return value
    
# --- NEW FILTER TO FIX TEMPLATE PARSING ERROR ---
@register.filter
def recommendation_slugify(value):
    """
    Converts recommendation strings like 'Strong Fit' or 'Low Match' 
    to lowercase slugs suitable for CSS classes (e.g., 'strong' or 'low').
    """
    if not isinstance(value, str):
        return ""
    
    value = value.lower()
    value = value.replace(' fit', '')
    value = value.replace(' match', '')
    return value