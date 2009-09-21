"""
Handle a Purchase Order payments.
"""
from django.utils.translation import ugettext as _
from bursar.gateway.base import BasePaymentProcessor, ProcessorResult, NOTSET

class PaymentProcessor(BasePaymentProcessor):

    def __init__(self, settings={}):
        working_settings={}
        working_settings.update(settings)
        super(PaymentProcessor, self).__init__('purchaseorder', working_settings)

    def can_refund(self):
        return True

    def capture_payment(self, testing=False, purchase=None, amount=NOTSET):
        """
        Purchase Orders are always successful.
        """
        if amount == NOTSET:
            amount = purchase.total

        payment = self.record_payment(purchase=purchase, amount=amount, 
            transaction_id="PO", reason_code='0')

        return ProcessorResult(self.key, True, _('Success'), payment)

