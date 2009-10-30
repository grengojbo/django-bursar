from django import template
from django.db import models

register = template.Library()

@register.simple_tag
def paypal_submit_form(gateway, purchase):
    return gateway.form(purchase)

paypal_submit_form.is_safe = True

@register.simple_tag
def paypal_submit_button_url(gateway, purchase):
    return gateway.submit_button_url(purchase)

paypal_submit_button_url.is_safe = True

@register.inclusion_tag('bursar/gateway/paypal_gateway/_paypal_simple_form.html')
def paypal_simple_form(gateway, purchase):
    return {
        'gateway' : gateway,
        'purchase' : purchase
    }
