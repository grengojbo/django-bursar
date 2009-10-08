from bursar.errors import GatewayError
from bursar.gateway.base import BasePaymentProcessor, ProcessorResult, NOTSET, PaymentPending
from bursar.numbers import trunc_decimal
from datetime import datetime
from decimal import Decimal
from django.template import loader, Context
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from satchmo_store.shop.models import Config
from tax.utils import get_tax_processor
from xml.dom import minidom
import random
import urllib2

class PaymentProcessor(BasePaymentProcessor):
    """
    Authorize.NET payment processing module
    You must have an account with authorize.net in order to use this module.
    
    Additionally, you must have ARB enabled in your account to use recurring billing.
    
    Settings:
        ARB: Enable ARB processing for setting up subscriptions.  Note: You 
            must have this enabled in your Authorize account for it to work.
        ARB_CONNECTION: Submit to URL for ARB transactions. This is the address 
            to submit live transactions for ARB.
        CAPTURE: Capture Payment immediately? IMPORTANT: If false, 
            a capture attempt will be made when the order is marked as shipped.
        CONNECTION: This is the address to submit live transactions.
        CONNECTION_TEST: Submit to Test URL.  A Quick note on the urls.
            If you are posting to https://test.authorize.net/gateway/transact.dll,
            and you are not using an account whose API login ID starts with
            "cpdev" or "cnpdev", you will get an Error 13 message. 
            Make sure you are posting to https://certification.authorize.net/gateway/transact.dll
            for test transactions if you do not have a cpdev or cnpdev.
        CREDITCHOICES: Available credit cards, as (key, name).  To add American Express, 
            use (('American Express', 'American Express'))
        EXTRA_LOGGING: Verbose Logs?
        LABEL: English name for this payment module on the checkout screens.
        LIVE: Accept real payments. NOTE: If you are testing, then you can use the cc# 
            4222222222222 to force a bad credit card response.  If you use that number 
            and a ccv of 222, that will force a bad ccv response from authorize.net
        LOGIN: (REQUIRED) Your authorize.net transaction login
        MODULE: Implementation module, fully qualified.
        SIMULATE: Force a test post?
        SSL: Use SSL for the checkout pages?
        STORE_NAME: (REQUIRED) The name of your store
        TRANKEY : (REQUIRED) Your authorize.net transaction key
        URL_BASE: The url base used for constructing urlpatterns which will use this module        
    """
    def __init__(self, settings={}):
        working_settings = {
            'CONNECTION' : 'https://secure.authorize.net/gateway/transact.dll',
            'CONNECTION_TEST' : 'https://test.authorize.net/gateway/transact.dll',
            'SSL' : False,
            'LIVE' : False,
            'SIMULATE' : False,
            'MODULE' : 'payment.modules.authorizenet',
            'LABEL' : _('Credit Cards'),
            'URL_BASE': r'^credit/',
            'CREDITCHOICES': (
                (('Visa','Visa')),
                (('Mastercard','Mastercard')),
                (('Discover','Discover'))),
            'CAPTURE' : True,
            'EXTRA_LOGGING' : False,
            'ARB' : False,
            'ARB_CONNECTION' : 'https://api.authorize.net/xml/v1/request.api',
            'ARB_CONNECTION_TEST' : 'https://apitest.authorize.net/xml/v1/request.api'
            }
        working_settings.update(settings)
        if not 'LOGIN' in working_settings:
            raise GatewayError('You must define a LOGIN for the AUTHORIZENET payment module.')

        if not 'STORE_NAME' in working_settings:
            raise GatewayError('You must define a STORE_NAME for the AUTHORIZENET payment module.')

        if not 'TRANKEY' in working_settings:
            raise GatewayError('You must provide a TRANKEY for the AUTHORIZENET payment module.')
            
        super(PaymentProcessor, self).__init__('authorizenet', working_settings)

    def authorize_payment(self, purchase=None, amount=NOTSET, testing=False):
        """Authorize a single payment.
        
        Returns: ProcessorResult
        """
        assert(purchase)
        if purchase.remaining == Decimal('0.00'):
            self.log_extra('%s is paid in full, no authorization attempted.', purchase)
            results = ProcessorResult(self.key, True, _("No charge needed, paid in full."))
        else:
            if amount == NOTSET:
                try:
                    pending = purchase.get_pending(self.key)
                    amount = pending.amount
                except PaymentPending.DoesNotExist:
                    amount = purchase.remaining
            self.log_extra('Authorizing payment of %s for %s', amount, purchase)

            standard = self.get_standard_charge_data(authorize=True, purchase=purchase, amount=amount)
            results = self.send_post(standard, testing, purchase=purchase)

        return results

    def can_authorize(self):
        return True

    def can_recur_bill(self):
        return True

    def capture_authorized_payment(self, authorization, testing=False, purchase=None, amount=NOTSET):
        """Capture a single payment"""
        assert(purchase)
        if purchase.authorized_remaining == Decimal('0.00'):
            self.log_extra('No remaining authorizations on %s', purchase)
            return ProcessorResult(self.key, True, _("Already complete"))

        self.log_extra('Capturing Authorization #%i of %s', authorization.id, amount)
        if amount==NOTSET:
            amount = authorization.amount
        data = self.get_prior_auth_data(authorization, amount=amount)
        results = None
        if data:
            results = self.send_post(data, testing, purchase=purchase)
        
        return results
        
    def capture_payment(self, testing=False, purchase=None, amount=NOTSET):
        """Process payments without an authorization step."""
        assert(purchase)
        recurlist = self.get_recurring_charge_data(purchase=purchase)
        if recurlist:
            success, results = self.process_recurring_subscriptions(recurlist, testing)
            if not success:
                self.log_extra('recur payment failed, aborting the rest of the module')
                return results

        if purchase.remaining == Decimal('0.00'):
            self.log_extra('%s is paid in full, no capture attempted.', purchase)
            results = ProcessorResult(self.key, True, _("No charge needed, paid in full."))
            self.record_payment(purchase=purchase)
        else:
            self.log_extra('Capturing payment for %s', purchase)
            
            standard = self.get_standard_charge_data(amount=amount, purchase=purchase)
            results = self.send_post(standard, testing, purchase=purchase)
            
        return results

    def get_prior_auth_data(self, authorization, amount=NOTSET):
        """Build the dictionary needed to process a prior auth capture."""
        trans = {'authorization' : authorization}
        remaining = authorization.remaining
        if amount == NOTSET or amount > remaining:
            if amount != NOTSET:
                self.log_extra('Adjusting auth amount from %s to %s', amount, remaining)
            amount = remaining
        
        balance = trunc_decimal(amount, 2)
        trans['amount'] = amount
        
        if self.is_live():
            conn = self.settings["CONNECTION"]
            self.log_extra('Using live connection.')
        else:
            testflag = 'TRUE'
            conn = self.settings["CONNECTION_TEST"]
            self.log_extra('Using test connection.')
            
        if self.settings["SIMULATE"]:
            testflag = 'TRUE'
        else:
            testflag = 'FALSE'

        trans['connection'] = conn

        trans['configuration'] = {
            'x_login' : self.settings["LOGIN"],
            'x_tran_key' : self.settings["TRANKEY"],
            'x_version' : '3.1',
            'x_relay_response' : 'FALSE',
            'x_test_request' : testflag,
            'x_delim_data' : 'TRUE',
            'x_delim_char' : '|',
            'x_type': 'PRIOR_AUTH_CAPTURE',
            'x_trans_id' : authorization.transaction_id
            }
        
        self.log_extra('prior auth configuration: %s', trans['configuration'])
                
        trans['transactionData'] = {
            'x_amount' : balance,
            }

        part1 = urlencode(trans['configuration']) 
        postdata = part1 + "&" + urlencode(trans['transactionData'])
        trans['postString'] = postdata
        
        self.log_extra('prior auth poststring: %s', postdata)
        trans['logPostString'] = postdata
        
        return trans
        
        
    def get_void_auth_data(self, authorization):
        """Build the dictionary needed to process a prior auth release."""
        trans = {
            'authorization' : authorization,
            'amount' : Decimal('0.00'),
        }

        if self.is_live():
            conn = self.settings['CONNECTION']
            self.log_extra('Using live connection.')
        else:
            testflag = 'TRUE'
            conn = self.settings["CONNECTION_TEST"]
            self.log_extra('Using test connection.')

        if self.settings['SIMULATE']:
            testflag = 'TRUE'
        else:
            testflag = 'FALSE'

        trans['connection'] = conn

        trans['configuration'] = {
            'x_login' : self.settings["LOGIN"],
            'x_tran_key' : self.settings["TRANKEY"],
            'x_version' : '3.1',
            'x_relay_response' : 'FALSE',
            'x_test_request' : testflag,
            'x_delim_data' : 'TRUE',
            'x_delim_char' : '|',
            'x_type': 'VOID',
            'x_trans_id' : authorization.transaction_id
            }

        self.log_extra('void auth configuration: %s', trans['configuration'])

        postdata = urlencode(trans['configuration']) 
        trans['postString'] = postdata

        self.log_extra('void auth poststring: %s', postdata)
        trans['logPostString'] = postdata

        return trans

    def get_recurring_charge_data(self, purchase=None, testing=False):
        """Build the list of dictionaries needed to process a recurring charge.
        
        Because Authorize can only take one subscription at a time, we build a list
        of the transaction dictionaries, for later sequential posting.
        """
        assert(purchase)
        if not self.settings['ARB']:
            return []
        
        # get all subscriptions from the order
        subscriptions = purchase.recurring_lineitems()
        
        if len(subscriptions) == 0:
            self.log_extra('No subscription items')
            return []

        # set up the base dictionary
        trans = {}

        if self.is_live():
            conn = self.settings['ARB_CONNECTION']
            self.log_extra('Using live recurring charge connection.')
        else:
            conn = self.settings['ARB_CONNECTION_TEST']
            self.log_extra('Using test recurring charge connection.')
                
        trans['connection'] = conn
        trans['config'] = {
            'merchantID' : self.settings['LOGIN'],
            'transactionKey' : self.settings['TRANKEY'],
            'shop_name' : self.settings['STORE_NAME'],
        }
        trans['purchase'] = purchase
        cc = self.purchase.credit_card
        trans['card'] = cc
        trans['card_expiration'] =  "%4i-%02i" % (cc.expire_year, cc.expire_month)
        
        translist = []
        # remove        
        for subscription in subscriptions:
            lineitem = subscription.lineitem

            subtrans = trans.copy()
            subtrans['subscription'] = subscription
            subtrans['product'] = lineitem.name

            if subscription.trial:
                trial_amount = lineitem.total
                trial_tax = lineitem.tax
                trial_shipping = lineitem.shipping
                amount = subscription.recurring_price()
                trial_occurrences = subscription.trial_times                
            else:
                trial_occurrences = 0
                trial_amount = Decimal('0.00')
                amount = subscription.recurring_price

            occurrences = subscription.recurring_times + subscription.trial_times
            if occurrences > 9999:
                occurrences = 9999

            subtrans['occurrences'] = subscription.recurring_times
            subtrans['trial'] = subscription.trial
            subtrans['trial_amount'] = trial_amount
            subtrans['trial_occurrences'] = trial_occurrances
            subtrans['amount'] = trunc_decimal(amount, 2)
            if trial:
                charged_today = trial_amount
            else:
                charged_today = amount
            
            charged_today = trunc_decimal(charged_today, 2)
                
            subtrans['charged_today'] = charged_today
            translist.append(subtrans)
            
        return translist
        
    def get_standard_charge_data(self, purchase=None, amount=NOTSET, authorize=False):
        """Build the dictionary needed to process a credit card charge"""
        assert(purchase)
        trans = {}
        if amount == NOTSET:
            amount = purchase.total
            
        balance = trunc_decimal(amount, 2)
        trans['amount'] = balance
        
        if self.is_live():
            conn = self.settings['CONNECTION']
            self.log_extra('Using live connection.')
        else:
            testflag = 'TRUE'
            conn = self.settings['CONNECTION_TEST']
            self.log_extra('Using test connection.')
            
        if self.settings['SIMULATE']:
            testflag = 'TRUE'
        else:
            testflag = 'FALSE'

        trans['connection'] = conn
            
        trans['authorize_only'] = authorize

        if not authorize:
            transaction_type = 'AUTH_CAPTURE'
        else:
            transaction_type = 'AUTH_ONLY'
                        
        trans['configuration'] = {
            'x_login' : self.settings['LOGIN'],
            'x_tran_key' : self.settings['TRANKEY'],
            'x_version' : '3.1',
            'x_relay_response' : 'FALSE',
            'x_test_request' : testflag,
            'x_delim_data' : 'TRUE',
            'x_delim_char' : '|',
            'x_type': transaction_type,
            'x_method': 'CC',
            }
        
        self.log_extra('standard charges configuration: %s', trans['configuration'])
        
        trans['custBillData'] = {
            'x_first_name' : purchase.first_name,
            'x_last_name' : purchase.last_name,
            'x_address': purchase.full_bill_street,
            'x_city': purchase.bill_city,
            'x_state' : purchase.bill_state,
            'x_zip' : purchase.bill_postal_code,
            'x_country': purchase.bill_country,
            'x_phone' : purchase.phone,
            'x_email' : purchase.email,
            }
    
        self.log_extra('standard charges configuration: %s', trans['custBillData'])
        
        invoice = "%s" % purchase.orderno
        failct = purchase.paymentfailures.count()
        if failct > 0:
            invoice = "%s_%i" % (invoice, failct)

        if not self.is_live():
            # add random test id to this, for testing repeatability
            invoice = "%s_test_%s_%i" % (invoice,  datetime.now().strftime('%m%d%y'), random.randint(1,1000000))
        
        card = purchase.credit_card
        cc = card.decryptedCC
        ccv = card.ccv
        if not self.is_live() and cc == '4222222222222':
            if ccv == '222':
                self.log_extra('Setting a bad ccv number to force an error')
                ccv = '1'
            else:
                self.log_extra('Setting a bad credit card number to force an error')
                cc = '1234'
        trans['transactionData'] = {
            'x_amount' : balance,
            'x_card_num' : cc,
            'x_exp_date' : card.expirationDate,
            'x_card_code' : ccv,
            'x_invoice_num' : invoice
            }

        part1 = urlencode(trans['configuration']) + "&"
        part2 = "&" + urlencode(trans['custBillData'])
        trans['postString'] = part1 + urlencode(trans['transactionData']) + part2
        
        redactedData = {
            'x_amount' : balance,
            'x_card_num' : card.display_cc,
            'x_exp_date' : card.expirationDate,
            'x_card_code' : "REDACTED",
            'x_invoice_num' : invoice
        }
        self.log_extra('standard charges transactionData: %s', redactedData)
        trans['logPostString'] = part1 + urlencode(redactedData) + part2
        
        return trans
        
    def process_recurring_subscriptions(self, recurlist, purchase=None, testing=False):
        """Post all subscription requests."""    
        assert(purchase)
        results = []
        for recur in recurlist:
            success, reason, response, subscription_id = self.process_recurring_subscription(recur, testing=testing)
            if success:
                if not testing:
                    payment = self.record_payment(purchase=purchase, amount=recur['charged_today'], transaction_id=subscription_id, reason_code=reason)
                    results.append(ProcessorResult(self.key, success, response, payment=payment))
            else:
                self.log.info("Failed to process recurring subscription, %s: %s", reason, response)
                break
        
        return success, results
        
    def process_recurring_subscription(self, data, testing=False):
        """Post one subscription request."""
        self.log_extra('Processing subscription: %s', data['product'].slug)
        
        t = loader.get_template('shop/checkout/authorizenet/arb_create_subscription.xml')
        ctx = Context(data)
        request = t.render(ctx)
        
        if self.settings['EXTRA_LOGGING']:
            data['redact'] = True
            ctx = Context(data)
            redacted = t.render(ctx)
            self.log_extra('Posting data to: %s\n%s', data['connection'], redacted)
        
        headers = {'Content-type':'text/xml'}
        conn = urllib2.Request(data['connection'], request, headers)
        try:
            f = urllib2.urlopen(conn)
            all_results = f.read()
        except urllib2.URLError, ue:
            self.log.error("error opening %s\n%s", data['connection'], ue)
            return (False, 'ERROR', _('Could not talk to Authorize.net gateway'), None)
        
        self.log_extra('Authorize response: %s', all_results)
        
        subscriptionID = None
        try:
            response = minidom.parseString(all_results)
            doc = response.documentElement
            reason = doc.getElementsByTagName('code')[0].firstChild.nodeValue
            response_text = doc.getElementsByTagName('text')[0].firstChild.nodeValue                
            result = doc.getElementsByTagName('resultCode')[0].firstChild.nodeValue
            success = result == "Ok"

            if success:
                #refID = doc.getElementsByTagName('refId')[0].firstChild.nodeValue
                subscriptionID = doc.getElementsByTagName('subscriptionId')[0].firstChild.nodeValue
        except Exception, e:
            self.log.error("Error %s\nCould not parse response: %s", e, all_results)
            success = False
            reason = "Parse Error"
            response_text = "Could not parse response"
            
        return success, reason, response_text, subscriptionID
        
        
    def release_authorized_payment(self, purchase=None, auth=None, testing=False):
        """Release a previously authorized payment."""
        assert(purchase)
        self.log_extra('Releasing Authorization #%i for %s', auth.id, purchase)
        data = self.get_void_auth_data(auth)
        results = None
        if data:
            results = self.send_post(data, testing, purchase=purchase)
            
        if results.success:
            auth.complete = True
            auth.save()
            
        return results
        
    def send_post(self, data, testing=False, purchase=None, amount=NOTSET):
        """Execute the post to Authorize Net.
        
        Params:
        - data: dictionary as returned by get_standard_charge_data
        - testing: if true, then don't record the payment
        
        Returns:
        - ProcessorResult
        """
        assert(purchase)
        self.log.info("About to send a request to authorize.net: %(connection)s\n%(logPostString)s", data)

        conn = urllib2.Request(url=data['connection'], data=data['postString'])
        try:
            f = urllib2.urlopen(conn)
            all_results = f.read()
            self.log_extra('Authorize response: %s', all_results)
        except urllib2.URLError, ue:
            self.log.error("error opening %s\n%s", data['connection'], ue)
            return ProcessorResult(self.key, False, _('Could not talk to Authorize.net gateway'))
            
        parsed_results = all_results.split(data['configuration']['x_delim_char'])
        response_code = parsed_results[0]
        reason_code = parsed_results[1]
        response_text = parsed_results[3]
        transaction_id = parsed_results[6]
        success = response_code == '1'
        if amount == NOTSET:
            amount = data['amount']

        payment = None
        if success and not testing:
            if data.get('authorize_only', False):
                self.log_extra('Success, recording authorization')
                payment = self.record_authorization(purchase=purchase, amount=amount, 
                    transaction_id=transaction_id, reason_code=reason_code)
            else:
                if amount <= 0:
                    self.log_extra('Success, recording refund')
                else:
                    self.log_extra('Success, recording payment')
                authorization = data.get('authorization', None)
                payment = self.record_payment(purchase=purchase, amount=amount, 
                    transaction_id=transaction_id, reason_code=reason_code, authorization=authorization)
            
        elif not testing:
            payment = self.record_failure(amount=amount, transaction_id=transaction_id, 
                reason_code=reason_code, details=response_text, purchase=purchase)

        self.log_extra("Returning success=%s, reason=%s, response_text=%s", success, reason_code, response_text)
        return ProcessorResult(self.key, success, response_text, payment=payment)

if __name__ == "__main__":
    """
    This is for testing - enabling you to run from the command line and make
    sure everything is ok
    """
    import os
    from livesettings import config_get_group

    # Set up some dummy classes to mimic classes being passed through Satchmo
    class testContact(object):
        pass
    class testCC(object):
        pass
    class testOrder(object):
        def __init__(self):
            self.contact = testContact()
            self.credit_card = testCC()
        def order_success(self):
            pass

    if not os.environ.has_key("DJANGO_SETTINGS_MODULE"):
        os.environ["DJANGO_SETTINGS_MODULE"]="satchmo_store.settings"

    settings_module = os.environ['DJANGO_SETTINGS_MODULE']
    settingsl = settings_module.split('.')
    settings = __import__(settings_module, {}, {}, settingsl[-1])

    sampleOrder = testOrder()
    sampleOrder.contact.first_name = 'Chris'
    sampleOrder.contact.last_name = 'Smith'
    sampleOrder.contact.primary_phone = '801-555-9242'
    sampleOrder.full_bill_street = '123 Main Street'
    sampleOrder.bill_postal_code = '12345'
    sampleOrder.bill_state = 'TN'
    sampleOrder.bill_city = 'Some City'
    sampleOrder.bill_country = 'US'
    sampleOrder.total = "27.01"
    sampleOrder.balance = "27.01"
    sampleOrder.credit_card.decryptedCC = '6011000000000012'
    sampleOrder.credit_card.expirationDate = "10/11"
    sampleOrder.credit_card.ccv = "144"

    from payment.tests import get_payment_settings
    authorize_settings = get_payment_settings()
    
    config_get_group('PAYMENT_AUTHORIZENET')
    if authorize_settings['LIVE']:
        print "Warning.  You are submitting a live order.  AUTHORIZE.NET system is set LIVE."
        
    processor = PaymentProcessor(authorize_settings.dict_values())
    processor.prepare_data(sampleOrder)
    purchase = sampleOrder.get_or_create_purchase()
    results = processor.process(testing=True, purchase=purchase)
    print results


