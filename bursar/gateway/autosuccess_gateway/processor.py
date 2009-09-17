from django.utils.translation import ugettext_lazy as _
from bursar.gateway.base import BasePaymentProcessor, ProcessorResult, NOTSET

class PaymentProcessor(BasePaymentProcessor):
    """
    Autosuccess Payment Module
    """
    def __init__(self, settings):
        super(PaymentProcessor, self).__init__('autosuccess', settings)

    def capture_payment(self, testing=False, purchase=None, amount=NOTSET):
        if not purchase:
            purchase = self.purchase

        if amount == NOTSET:
            amount = purchase.total

        payment = self.record_payment(purchase=purchase, 
            amount=amount, 
            transaction_id="AUTO", 
            reason_code='0')

        return ProcessorResult(self.key, True, _('Success'), payment)
