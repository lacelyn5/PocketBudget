from decimal import Decimal, InvalidOperation
from django import template

register = template.Library()


@register.filter
def money(value):
    """Format money values consistently for templates."""
    try:
        amount = Decimal(value or 0)
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal('0.00')
    formatted = f'{amount:,.2f}'
    return f'{formatted} zł'


@register.filter
def percent(value):
    try:
        amount = Decimal(value or 0)
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal('0')
    return f'{amount:.1f}%'
