from decimal import Decimal
from django import forms
from django.utils.translation import ugettext as _

class IpnTestForm(forms.Form):
    invoice = forms.CharField(label=_('Purchase #'), required=True, max_length=20)
    amount = forms.DecimalField(label=_('Amount'), initial=Decimal('0.00'))
    transaction = forms.CharField(label=_('Transaction ID'), required=True, max_length=45)
    note = forms.CharField(_("Note"), required=False)
    
    