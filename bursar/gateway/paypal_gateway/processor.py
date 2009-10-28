"""PayPal Gateway

To use this, the processor must be initialized with at least a dictionary 
containing the following keys::

* BUSINESS - The email address of the receiving paypal account (if LIVE is true).
* BUSINESS_TEST - The email address of the test receiving paypal account (if LIVE is false).

It should also contain a key for "RETURN_ADDRESS", a named view where the customer will
be returned after a successful purchase.  In Satchmo, this is "PAYPAL_satchmo_checkout-success"

"""

from bursar.gateway.base import HeadlessPaymentProcessor
from bursar.models import Payment, Purchase
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

import urllib2

PAYMENT_CMD = {
    'BUY_NOW' : '_xclick',
    'CART' : '_cart',
    'SUBSCRIPTION' : '_xclick-subscriptions_'
}

NO_SHIPPING = {
    'NO' : '1',
    'YES' : '0'
}

NO_NOTE = {
    'NO' : "1",
    'YES' : "0"
}

RECURRING_PAYMENT = {
    'YES' : "1",
    'NO' : "0"
}


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
            
            # use SSL for checkout
            'SSL' : False,
            
            'LOCALE' : 'US',
            
            # Reattempt on fail
            'REATTEMPT' : True,
            
            'LABEL' : _('PayPal'),
            'EXTRA_LOGGING' : False,
            }
        working_settings.update(settings)                    

        super(PaymentProcessor, self).__init__('paypal', working_settings)
        if self.is_live():
            self.require_settings("POST_URL", "BUSINESS", "RETURN_ADDRESS")
        else:
            self.require_settings("POST_TEST_URL", "BUSINESS_TEST", "RETURN_ADDRESS")
    

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

    @property
    def ipn_url(self):
        prefix = "http"
        if self.settings['SSL']:
            prefix += "s"
        base = prefix + "://" + Site.objects.get_current().domain

        view_url = urlresolvers.reverse('PAYPAL_GATEWAY_ipn')
        if base.endswith("/"):
            base = base[:-1]
        if view_url.startswith('/'):
            view_url = view_url[1:]

        url = base + '/' + view_url
        self.log.debug('IPN URL=%s', url)
        return url


    def submit_url(self):
        if self.is_live():
            url = self.settings['POST_URL']
        else:
            url = self.settings['POST_TEST_URL']
        return url


    def form(self, purchase):
        """Render a form for submission to PayPal"""
        live = self.is_live()
        pp = self.settings
        if live:
            self.log_extra("live purchase on %s", self.key)
            account = pp['BUSINESS']
        else:
            account = pp['BUSINESS_TEST']

        address = pp['RETURN_ADDRESS']
                
        submit = {
            'business' : account,
            'currency_code' : pp['CURRENCY_CODE'],
            'return' : address,
            'notify_url' : self.ipn_url
        }
        
        #TODO: eventually need to work out the terrible PayPal shipping stuff
        #      for now, we are saying "no shipping" and adding all shipping as
        #      a handling charge.
        submit['no_shipping'] = NO_SHIPPING['YES']
        submit['handling_cart'] = purchase.shipping
        submit['tax_cart'] = purchase.tax
        
        # Locale
        submit['lc'] = self.settings['LOCALE']
        submit['invoice'] = purchase.id
        
        recuritems = purchase.recurring_lineitems()
        if len(recuritems) > 1:
            self.log.warn("Cannot have more than one subscription in one order for paypal.  Only processing the first one for %s", purchase)

        if len(recuritems) > 0:
            recur = recuritems[0]
            submit['src'] = '1'
            submit['cmd'] = PAYMENT_CMD['SUBSCRIPTION']
            submit['item_name'] = recur.product.name
            submit['item_number'] = recur.product.sku
            submit['no_note'] = NO_NOTE['YES']
            submit['bn'] = 'PP-SubscriptionsBF'
            
            # initial trial
            if recur.trial:
                submit['a1'] = recur.trial_price
                submit['p1'] = recur.trial_length
                submit['t1'] = recur.expire_unit
                
            if recur.trial_times > 1:
                submit['a2'] = recur.trial_price
                submit['p2'] = recur.trial_length
                submit['t2'] = recur.expire_unit
                
            # subscription price
            submit['a3'] = recur.price
            submit['p3'] = recur.expire_length
            submit['t3'] = recur.expire_unit
            submit['srt'] = recur.recurring_times
            submit['modify'] = '1'  # new or modify subscription
            
            if self.settings['REATTEMPT']:
                reattempt = '1'
            else:
                reattempt = '0'
            submit['sra'] = reattempt
            
        else:
            submit['cmd'] = PAYMENT_CMD['CART']
            submit['upload'] = '1'

            if purchase.partially_paid:
                submit['item_name_1'] = "Remaining Balance for order #%(invoice)s" % {'invoice': purchase.id}
                submit['amount_1'] = str(purchase.remaining)
                submit['quantity_1'] = '1'
            else:
                ix = 1
                for item in purchase.lineitems.all():
                    submit['item_name_%i' % ix] = item.name
                    submit['amount_%i' % ix] = item.unit_price
                    submit['quantity_%i' % ix] = item.int_quantity
                    ix += 1
                    
        if purchase.bill_street1:
            submit['first_name'] = purchase.first_name
            submit['last_name'] = purchase.last_name
            submit['address1'] = purchase.bill_street1
            submit['address2'] = purchase.bill_street2
            submit['city'] = purchase.bill_city
            submit['country'] = purchase.bill_country
            submit['zip'] = purchase.bill_postal_code
            submit['email'] = purchase.email
            submit['address_override'] = '0'
            # only U.S. abbreviations may be used here
            if purchase.bill_country.lower() == 'us' and len(purchase.bill_state) == 2:
                submit['state'] = purchase.bill_state
                
        ret = []
        for key, val in submit.items():
            ret.append('<input type="hidden" name="%s" value="%s">' % (key, val))
        return mark_safe("\n".join(ret))

