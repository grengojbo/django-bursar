from bursar import signals
from bursar.fields import CurrencyField
from bursar.models import Authorization, Payment, PaymentFailure, PaymentPending, Purchase
from datetime import datetime
from decimal import Decimal
from django.utils.translation import ugettext_lazy as _
from livesettings import config_get_group
from satchmo_store.shop.models import Order, OrderStatus
import logging

log = logging.getLogger('bursar.gateway.base')

NOTSET = object()

class BasePaymentProcessor(object):

    def __init__(self, key, settings):
        self.key = key
        self.settings = settings
        self.log = logging.getLogger('bursar.gateway.' + key)

    def allowed(self, user, amount):
        """Allows different payment processors to be allowed for certain situations."""
        return True
        
    def authorize_and_release(self, purchase=None, amount=NOTSET, testing=False):
        assert(purchase)
        if amount == NOTSET:
            amount = Decimal('0.01')
        self.log_extra('authorize_and_release for purchase on order #%i, %s', purchase.orderno, amount)
        result = self.authorize_payment(testing=testing, purchase=purchase, amount=amount)
        if result.success:
            auths = purchase.authorizations.filter(complete=False).order_by('-id')
            if auths.count() > 0:
                auth = auths[0]
            self.log_extra('releasing successful authorize_and_release for purchase on order #%i [%s], %s.  AUTH', 
                purchase.orderno,  amount, auth.transaction_id)
            return self.release_authorized_payment(purchase=purchase, auth=auth, testing=testing)
        else:
            self.log_extra('early authorization was not successful for: %s', purchase)
            return result

    def authorize_payment(self, testing=False, purchase=None, amount=NOTSET):
        """Authorize a single payment, must be overridden to function"""
        self.log.warn('Module does not implement authorize_payment: %s', self.key)
        return ProcessorResult(False, _("Not Implemented"), None, None)

    def can_authorize(self):
        return False

    def can_process(self):
        return True

    def can_refund(self):
        return False

    def can_recur_bill(self):
        return False

    def capture_authorized_payments(self, purchase=None):
        """Capture all outstanding payments for this processor.  This is usually called by a 
        listener which watches for a 'shipped' status change on the Order."""
        assert(purchase)
        results = []
        if self.can_authorize():
            auths = purchase.authorizations.filter(method__exact=self.key, complete=False)
            self.log_extra('Capturing %i %s authorizations for purchase on order #%s', auths.count(), self.key, purchase.orderno)
            for auth in auths:
                results.append(self.capture_authorized_payment(auth, purchase=Purchase))
                
        return results

    def capture_authorized_payment(self, authorization, testing=False, purchase=None, amount=NOTSET):
        """Capture a single payment, must be overridden to function"""
        self.log.warn('Module does not implement capture_payment: %s', self.key)
        return ProcessorResult(False, _("Not Implemented"))

    def capture_payment(self, testing=False, purchase=None, amount=NOTSET):
        """Capture payment without an authorization step.  Override this one."""
        self.log.warn('Module does not implement authorize_and_capture: %s', self.key)
        return ProcessorResult(False, _("Not Implemented"))
        
    def create_pending_payment(self, purchase=None, amount=NOTSET):
        assert(purchase)
        recorder = PaymentRecorder(purchase, self.key)
        return recorder.create_pending(amount=amount)

    def is_live(self):
        return self.settings['LIVE']

    def log_extra(self, msg, *args):
        """Send a log message if EXTRA_LOGGING is set in settings."""
        if self.settings['EXTRA_LOGGING']:
            self.log.info("(Extra logging) " + msg, *args)
            
    def pending_amount(self, purchase):
        try:
            pending = purchase.get_pending(self.key)
            amount = pending.amount
        except PaymentPending.DoesNotExist:
            amount = purchase.total
        return amount

    def process(self, purchase, testing=False):
        """This will process the payment."""
        if self.can_authorize() and not self.settings['CAPTURE']:
            self.log_extra('Authorizing payment on order #%i', purchase.orderno)
            return self.authorize_payment(testing=testing)
        else:
            self.log_extra('Capturing payment on order #%s', purchase.orderno)
            return self.capture_payment(purchase=purchase, testing=testing)
            
    def record_authorization(self, amount=NOTSET, transaction_id="", reason_code="", purchase=None):
        """
        Convert a pending payment into a real authorization.
        """
        assert(purchase)
        recorder = PaymentRecorder(purchase, self.key)
        recorder.transaction_id = transaction_id
        recorder.reason_code = reason_code
        return recorder.authorize_payment(amount=amount)

    def record_failure(self, amount=NOTSET, transaction_id="", reason_code="", 
        authorization=None, purchase=None, details=""):
        """
        Add an PaymentFailure record
        """
        assert(purchase)
        log.debug('record_failure for %s', purchase)

        recorder = PaymentRecorder(purchase, self.key)
        recorder.transaction_id = transaction_id
        recorder.reason_code = reason_code
        recorder.record_failure(amount, details=details, authorization=authorization)

    def record_payment(self, amount=NOTSET, transaction_id="", reason_code="", authorization=None, purchase=None):
        """
        Convert a pending payment or an authorization.
        """
        if not purchase:
            purchase = authorization.purchase
        recorder = PaymentRecorder(purchase, self.key)
        recorder.transaction_id = transaction_id
        recorder.reason_code = reason_code

        if authorization:
            payment = recorder.capture_authorized_payment(authorization, amount=amount)
            authorization.complete=True
            authorization.save()

        else:
            payment = recorder.capture_payment(amount=amount)

        return payment

    def release_authorized_payment(self, purchase=None, auth=None, testing=False):
        """Release a previously authorized payment."""
        self.log.warn('Module does not implement released_authorized_payment: %s', self.key)
        return ProcessorResult(False, _("Not Implemented"))

class HeadlessPaymentProcessor(BasePaymentProcessor):
    """A payment processor which doesn't actually do any processing directly.
    
    This is used for payment providers such as PayPal and Google, which are entirely
    view/form based.
    """
    
    def can_process(self):
        return False

class PaymentRecorder(object):
    """Manages proper recording of pending payments, payments, and authorizations."""
    
    def __init__(self, purchase, key):
        self.purchase = purchase
        self.key = key
        self._amount = NOTSET
        self.transaction_id = ""
        self.reason_code = ""
        self.payment = None
        self.pending = None
        
    def _set_amount(self, amount):
        if amount != NOTSET:
            self._amount = amount

    def _get_amount(self):
        if self._amount == NOTSET:
            return self.purchase.total
        else:
            return self._amount

    amount = property(fset=_set_amount, fget=_get_amount)
            
    def authorize_payment(self, amount=NOTSET):
        """Make an authorization, using the existing pending payment if found"""
        self.amount = amount
        log.debug("Recording %s authorization of %s for #%s", self.key, self.amount, self.purchase.orderno)

        self.pending = self.purchase.get_pending(self.key, raises=False)

        if self.pending:
            self.payment = Authorization()
            self.payment.capture = self.pending.capture
            
            if amount == NOTSET:
                self.set_amount_from_pending()
            
        else:
            log.debug("No pending %s authorizations for %s", self.key, self.purchase)
            self.payment = Authorization(
                purchase=self.purchase, 
                method=self.key)

        self.cleanup()
        return self.payment

    def capture_authorized_payment(self, authorization, amount=NOTSET):
        """Convert an authorization into a payment."""
        self.amount = amount
        log.debug("Recording %s capture of authorization #%i for #%s", self.key, authorization.id, authorization.purchase.orderno)

        self.payment = authorization.capture
        self.payment.success=True
        self.payment.save()
        self.cleanup()
        return self.payment

    def capture_payment(self, amount=NOTSET):
        """Make a direct payment without a prior authorization, using the existing pending payment if found."""
        self.amount = amount

        self.pending = self.purchase.get_pending(self.key, raises=False)
        
        if self.pending:
            self.payment = self.pending.capture
            log.debug("Using linked payment: %s", self.payment)
            self.payment.success = True

            if amount == NOTSET:
                self.set_amount_from_pending()

        else:
            log.debug("No pending %s payments for %s", self.key, self.purchase)
        
            self.payment = Payment(
                purchase=self.purchase,
                method=self.key,
                success=True)
                
        log.debug("Recorded %s payment of %s for #%s", self.key, self.amount, self.purchase.orderno)
        self.cleanup()
        return self.payment
        
    def record_failure(self, amount=NOTSET, details="", authorization=None):
        log.info('Recording a payment failure: order #%i, code %s\nmessage=%s', self.purchase.orderno, self.reason_code, details)
        self.amount = amount
            
        failure = PaymentFailure.objects.create(purchase=self.purchase, 
            details=details, 
            transaction_id=self.transaction_id,
            amount = self.amount,
            payment = self.key,
            reason_code = self.reason_code
        )
        return failure
    
    def cleanup(self):
        if self.pending:
            pending = self.pending
            self.payment.capture = pending.capture
            self.payment.purchase = pending.purchase
            self.payment.method = pending.method
            self.payment.details = pending.details

            # delete any extra pending payments
            for p in self.purchase.paymentspending.all():
                if p != pending and p.capture.transaction_id=='LINKED':
                    p.capture.delete()
                p.delete()

        self.payment.reason_code=self.reason_code
        self.payment.transaction_id=self.transaction_id
        self.payment.amount=self.amount

        self.payment.time_stamp = datetime.now()
        self.payment.save()

        purchase = self.payment.purchase

        signals.payment_complete.send(sender='bursar', purchase=self.purchase, payment=self.payment)
        log.debug('cleanup details: %s', self.payment)

    def create_pending(self, amount=NOTSET):
        """Create a placeholder payment entry for the purchase.  
        This is done by step 2 of the payment process."""
        if amount == NOTSET:
            amount = self.purchase.remaining
            
        self.amount = amount

        pendings = self.purchase.paymentspending
        ct = pendings.count()
        if ct > 0:
            log.debug("Deleting %i expired pending payment entries for order #%s", ct, self.purchase.orderno)

            for pending in pendings.all():
                if pending.capture.transaction_id=='LINKED':
                    pending.capture.delete()
                pending.delete()
        
        log.debug("Creating pending %s payment of %s for %s", self.key, amount, self.purchase)

        self.pending = PaymentPending.objects.create(purchase=self.purchase, amount=amount, method=self.key)
        return self.pending

    def set_amount_from_pending(self):
        """Try to figure out how much to charge. If it is set on the "pending" charge use that
        otherwise use the purchase total."""
        amount = self.pending.amount
                
        # otherwise use the purchase total.
        if amount == Decimal('0.00'):
            amount = self.purchase.total

        log.debug('Settings amount from pending=%s', self.purchase.total)                    
        self.amount = amount

class ProcessorResult(object):
    """The result from a processor.process call"""

    def __init__(self, processor, success, message, payment=None):
        """Initialize with:

        processor - the key of the processor setting the result
        success - boolean
        message - a lazy string label, such as _('OK)
        payment - an Payment or Authorization
        """
        self.success = success
        self.processor = processor
        self.message = message
        self.payment = payment

    def __unicode__(self):
        if self.success:
            yn = _('Success')
        else:
            yn = _('Failure')

        return u"ProcessorResult: %s [%s] %s" % (self.processor, yn, self.message)
