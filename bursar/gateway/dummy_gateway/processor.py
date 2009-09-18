"""
This is a stub and used as the default processor.
It doesn't do anything but it can be used to build out another
interface.

See the authorizenet module for the reference implementation
"""
from django.utils.translation import ugettext_lazy as _
from bursar.gateway.base import BasePaymentProcessor, ProcessorResult, NOTSET

class PaymentProcessor(BasePaymentProcessor):

    def __init__(self, settings={}):
        default_settings = {
            'SSL': False,
            'LIVE': False,
            'LABEL': _('Payment test module'),
            'CREDITCHOICES': ('Visa', 'Mastercard', 'Discover', 'American Express'),
            'CAPTURE': True,
            'AUTH_EARLY': False,
            'EXTRA_LOGGING': False,
        }
        super(PaymentProcessor, self).__init__('dummy', default_settings, settings)

    def authorize_payment(self, purchase=None, testing=False, amount=NOTSET):
        """
        Make an authorization for an purchase.  This payment will then be captured when the purchase
        is set marked 'shipped'.
        """
        assert(purchase)
        if amount == NOTSET:
            amount = self.pending_amount(purchase)
        
        cc = purchase.credit_card
        if cc:
            ccn = cc.decryptedCC
            ccv = cc.ccv
            if ccn == '4222222222222':
                if ccv == '222':
                    self.log_extra('Bad CCV forced')
                    payment = self.record_failure(amount=amount, transaction_id='2', 
                        reason_code='2', details='CCV error forced')                
                    return ProcessorResult(self.key, False, _('Bad CCV - order declined'), payment)
                else:
                    self.log_extra('Setting a bad credit card number to force an error')
                    payment = self.record_failure(amount=amount, transaction_id='2', 
                        reason_code='2', details='Credit card number error forced')                
                    return ProcessorResult(self.key, False, _('Bad credit card number - order declined'), payment)

        orderauth = self.record_authorization(amount=amount, reason_code="0", purchase=purchase)
        return ProcessorResult(self.key, True, _('Success'), orderauth)

    def can_authorize(self):
        return True

    def capture_payment(self, testing=False, purchase=None, amount=NOTSET):
        """
        Process the transaction and return a ProcessorResult:

        Example:
        >>> from livesettings import config_get_group
        >>> settings = config_get_group('GATEWAY_DUMMY')
        >>> from bursar.gateway.dummy.processor import PaymentProcessor
        >>> processor = PaymentProcessor(settings.dict_values())
        # If using a normal payment gateway, data should be an Order object.
        >>> data = {}
        >>> processor.prepare_data(data)
        >>> processor.process()
        ProcessorResult: DUMMY [Success] Success
        """
        
        payment = self.record_payment(amount=amount, reason_code="0", purchase=purchase)
        return ProcessorResult(self.key, True, _('Success'), payment)


    def capture_authorized_payment(self, authorization, amount=NOTSET, purchase=None):
        """
        Capture a prior authorization
        """
        assert(purchase)
        if amount == NOTSET:
            amount = authorization.amount
            
        payment = self.record_payment(amount=amount, reason_code="0", 
            transaction_id="dummy", authorization=authorization, purchase=purchase)
        
        return ProcessorResult(self.key, True, _('Success'), payment)
        
    def release_authorized_payment(self, purchase=None, auth=None, testing=False):
        """Release a previously authorized payment."""
        auth.complete = True
        auth.save()
        return ProcessorResult(self.key, True, _('Success'))
