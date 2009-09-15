from django import template
from django.utils import translation
from livesettings import config_get_group, config_get
from satchmo_store.shop.models import ORDER_STATUS 

register = template.Library()

def payment_label(value):
    """convert a payment key into its translated text"""
    
    payments = config_get("GATEWAY", "MODULES")
    for mod in payments.value:
        config = config_get_group(mod)
        if config.KEY.value == value:
            return translation.ugettext(config.LABEL)
    return value.capitalize()

register.filter(payment_label)

def order_payment_summary(order, paylink=False):
    """Output a formatted block giving attached payment details."""
   
    return {'order' : order,
        'paylink' : paylink}

register.inclusion_tag('payment/_order_payment_summary.html')(order_payment_summary)

def status_label(value):
    """convert a order status into its translated text"""
   
    for status, descr in ORDER_STATUS:
        if status == value:
            return descr
    return value

register.filter(status_label)
