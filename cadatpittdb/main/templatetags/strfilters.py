from django import template
from django.template.defaulttags import register
from django.template.defaultfilters import stringfilter
from datetime import datetime

register = template.Library()


@register.filter
def truncate_date(datetime):
    """Removes the time component from datetime str """
    date = datetime.strftime("%B %d, %Y")
    return date
