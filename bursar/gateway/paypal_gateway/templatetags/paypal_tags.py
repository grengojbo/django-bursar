from django import template
from django.db import models

register = template.Library()

@register.inclusion_tag("bursar/gateway/paypal_gateway/_paypal_submit_form.html")
def paypal_submit_form(gateway, purchase):
    context = gateway.prepare_submit_form(purchase)
    return context
