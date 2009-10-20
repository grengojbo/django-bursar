"""PayPal Gateway

To use this, the processor must be initialized with at least a dictionary 
containing the following keys::

* BUSINESS - The email address of the receiving paypal account (if LIVE is true).
* BUSINESS_TEST - The email address of the test receiving paypal account (if LIVE is false).

It should also contain a key for "RETURN_ADDRESS", a named view where the customer will
be returned after a successful purchase.  In Satchmo, this is "PAYPAL_satchmo_checkout-success"

"""

from bursar.errors import GatewayError
from bursar.gateway.base import HeadlessPaymentProcessor
from bursar.models import Payment, Purchase
from django.utils.http import urlencode
from django.utils.translation import ugettext as _
import urllib2

class PaymentProcessor(HeadlessPaymentProcessor):
    """Paypal payment processor"""

    def __init__(self, settings={}):
        working_settings = {
            # Currency code for Paypal transactions.
            'CURRENCY_CODE' : 'USD',  
            
            # 'The Paypal URL for real transaction posting'
            'POST_URL' : "https://www.paypal.com/cgi-bin/webscr",
            
            # The Paypal URL for test transaction posting
            'POST_TEST_URL' : "https://www.sandbox.paypal.com/cgi-bin/webscr", 
            
            #a named view where the customer will
            #be returned after a successful purchase
            'RETURN_ADDRESS' : "",
            
            # Accept real payments
            'LIVE' : False,
            
            'LABEL' : _('PayPal'),
            'EXTRA_LOGGING' : False,
            }
        working_settings.update(settings)
        if working_settings['LIVE']:
            for key in ("POST_URL", "BUSINESS"):
                if not key in working_settings and working_settings[key]:
                    raise GatewayError('Paypal processor needs a %s in its settings.' % key)
        else:
            for key in ("POST_TEST_URL", "BUSINESS_TEST"):
                if not key in working_settings and working_settings[key]:
                    raise GatewayError('Paypal processor needs a %s in its settings.' % key)
                    
        if not working_settings.get('RETURN_ADDRESS', ''):
            self.log.warn('RETURN_ADDRESS should be specified in your Paypal settings.')

        super(PaymentProcessor, self).__init__('paypal', working_settings)

    def accept_ipn(self, invoice, amount, transaction_id, note=""):
        """Mark a PayPal payment as successfully paid - due to a successful IPN confirmation."""
        
        # skip if we've already handled this one
        if Payment.objects.filter(transaction_id=transaction_id).count() > 0:
            self.log.warn('IPN received for transaction #%s, already processed', transaction_id)
        else:
            self.log_extra('Successful IPN on invoice #%s, transaction #%s', invoice, transaction_id)
            # invoice may have a suffix due to retries
            invoice = invoice.replace('-', '_')
            invoice = invoice.split('_')[0]
            purchase = Purchase.objects.get(pk=invoice)
            payment = self.record_payment(
                amount = amount,
                transaction_id = transaction_id,
                purchase = purchase
                )

            if note:
                payment.add_note(_('---Comment via Paypal IPN---') + u'\n' + note)
                self.log_extra("Saved order notes from PayPal: %s", note)

            #TODO: verify - is this right? not sure if I should be setting them to "completed"
            for item in purchase.recurring_lineitems():
                if not item.completed:
                    self.log_extra("Marking item: %s complete", item)
                    item.completed = True
                    item.save()

    def confirm_ipn_data(self, data):
        """Test an IPN from PayPal.  If `force` is set, then skip the post."""

        self.log_extra("PayPal IPN data: ", repr(data))
        
        if self.is_live():
            self.log.debug("Live IPN on %s", self.key)
            url = self.settings['POST_URL']
        else:
            self.log.debug("Test IPN on %s", self.key)
            url = self.settings['POST_TEST_URL']
        
        data['cmd'] = "_notify-validate"
        params = urlencode(data)

        req = urllib2.Request(url)
        req.add_header("Content-type", "application/x-www-form-urlencoded")
        fo = urllib2.urlopen(req, params)

        ret = fo.read()
        if ret == "VERIFIED":
            self.log.info("PayPal IPN data verification was successful.")
            return True

        self.log.info("PayPal IPN data verification failed.")
        self.log_extra("HTTP code %s, response text: '%s'" % (fo.code, ret))
        return False

