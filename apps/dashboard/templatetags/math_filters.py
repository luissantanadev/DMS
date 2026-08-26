from django import template

register = template.Library()


@register.filter(name="percentage")
def percentage(value, total):
    """Calculate percentage of value relative to total."""
    if total == 0:
        return "0"
    try:
        result = (int(value) / int(total)) * 100
        return str(int(result))
    except (ValueError, TypeError, ZeroDivisionError):
        return "0"
