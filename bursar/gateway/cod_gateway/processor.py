"""
Handle a cash-on-delivery payment.
"""
from django.utils.translation import ugettext as _
from bursar.gateway.base import BasePaymentProcessor, ProcessorResult, NOTSET

class PaymentProcessor(BasePaymentProcessor):
    """COD Payment Processor"""

    def __init__(self, settings={}):
        working_settings = {
            'SSL': False,
            'LIVE': False,
            'LABEL': _('Payment COD Module'),
            'CAPTURE': True,
            'AUTH_EARLY': False,
            'EXTRA_LOGGING': False,
        }
        working_settings.update(settings)
        super(PaymentProcessor, self).__init__('cod', working_settings)

    def capture_payment(self, testing=False, purchase=None, amount=NOTSET):
        """
        COD is always successful.
        """
        assert(purchase)
        if amount == NOTSET:
            amount = purchase.total

        payment = self.record_payment(amount=amount, 
            transaction_id=self.key, reason_code='0', purchase=purchase)

        return ProcessorResult(self.key, True, _('Success'), payment)

