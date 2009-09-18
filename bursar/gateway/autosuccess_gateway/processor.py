from bursar.gateway.base import BasePaymentProcessor, ProcessorResult, NOTSET
from django.utils.translation import ugettext_lazy as _
import logging

log = logging.getLogger('bursar.gateway.autosuccess_gateway')

class PaymentProcessor(BasePaymentProcessor):
    """
    Autosuccess Payment Module
    """
    def __init__(self, settings={}):
        default_settings = {
            'SSL': False,
            'LIVE': False,
            'LABEL': _('Payment Autosuccess Module'),
            'CAPTURE': True,
            'AUTH_EARLY': False,
            'EXTRA_LOGGING': False,
        }
        super(PaymentProcessor, self).__init__('autosuccess', default_settings, settings)

    def capture_payment(self, testing=False, purchase=None, amount=NOTSET):
        assert(purchase)
        if amount == NOTSET:
            amount = purchase.total
            
        log.debug('Capturing payment of %s', amount)

        payment = self.record_payment(purchase=purchase, 
            amount=amount, 
            transaction_id=self.key, 
            reason_code='0')

        return ProcessorResult(self.key, True, _('Success'), payment)
