from bursar.config import credit_choices, labelled_gateway_choices
from django import forms
from django.db import models
from django.db.models.fields import DecimalField
from widgets import CurrencyWidget

class CreditChoiceCharField(models.CharField):

    def __init__(self, choices="__DYNAMIC__", *args, **kwargs):
        if choices == "__DYNAMIC__":
            kwargs['choices'] = credit_choices()

        super(CreditChoiceCharField, self).__init__(*args, **kwargs)


class CurrencyField(DecimalField):

    def __init__(self, *args, **kwargs):
        self.places = kwargs.pop('display_decimal', 2)
        super(CurrencyField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {
            'max_digits': self.max_digits,
            'decimal_places': self.decimal_places,
            'form_class': forms.DecimalField,
            'widget': CurrencyWidget,
        }
        defaults.update(kwargs)
        return super(CurrencyField, self).formfield(**defaults)


class PaymentChoiceCharField(models.CharField):

    def __init__(self, choices="__DYNAMIC__", *args, **kwargs):
        if choices == "__DYNAMIC__":
            kwargs['choices'] = labelled_gateway_choices()

        super(PaymentChoiceCharField, self).__init__(*args, **kwargs)
        
class RoundedDecimalField(forms.Field):
    def clean(self, value):
        """
        Normalize the field according to cart normalizing rules.
        """
        cartplaces = config_value('SHOP', 'CART_PRECISION')
        roundfactor = config_value('SHOP', 'CART_ROUNDING')    

        if not value or value == '':
            value = Decimal(0)

        try:
            value = round_decimal(val=value, places=cartplaces, roundfactor=roundfactor, normalize=True)
        except RoundedDecimalError:
            raise forms.ValidationError(_('%(value)s is not a valid number') % {'value' : value})

        return value

class PositiveRoundedDecimalField(RoundedDecimalField):
    """
    Normalize the field according to cart normalizing rules and force it to be positive.
    """
    def clean(self, value):
        value = super(PositiveRoundedDecimalField, self).clean(value)
        if value<0:
            log.debug('bad val: %s', value)
            raise forms.ValidationError(_('Please enter a positive number'))

        return value

