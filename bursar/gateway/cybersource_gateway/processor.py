from bursar.gateway.base import BasePaymentProcessor, ProcessorResult, NOTSET
from bursar.numbers import trunc_decimal
from decimal import Decimal
from django.template import Context, loader
from django.utils.translation import ugettext_lazy as _

import urllib2
try:
    from xml.etree.ElementTree import fromstring
except ImportError:
    from elementtree.ElementTree import fromstring

# Response codes available at:
# http://apps.cybersource.com/library/documentation/sbc/api_guide/SB_API.pdf
CYBERSOURCE_RESPONSES = {
    '100' : 'Successful transaction.',
    '101' : 'The request is missing one or more required fields.',
    '102' : 'One or more fields in the request contains invalid data.',
    '104' : 'The merchantReferenceCode sent with this authorization request matches the merchantReferenceCode of another authorization request that you sent in the last 15 minutes.',
    '150' : 'Error: General system failure. ',
    '151' : 'Error: The request was received but there was a server timeout. This error does not include timeouts between the client and the server.',
    '152' : 'Error: The request was received, but a service did not finish running in time.',
    '201' : 'The issuing bank has questions about the request. You do not receive an authorization code in the reply message, but you might receive one verbally by calling the processor.',
    '202' : 'Expired card. You might also receive this if the expiration date you provided does not match the date the issuing bank has on file.',
    '203' : 'General decline of the card. No other information provided by the issuing bank.',
    '204' : 'Insufficient funds in the account.',
    '205' : 'Stolen or lost card.',
    '207' : 'Issuing bank unavailable.',
    '208' : 'Inactive card or card not authorized for card-not-present transactions.',
    '210' : 'The card has reached the credit limit. ',
    '211' : 'Invalid card verification number.',
    '221' : 'The customer matched an entry on the processor\'s negative file.',
    '231' : 'Invalid account number.',
    '232' : 'The card type is not accepted by the payment processor.',
    '233' : 'General decline by the processor.',
    '234' : 'There is a problem with your CyberSource merchant configuration.',
    '235' : 'The requested amount exceeds the originally authorized amount. Occurs, for example, if you try to capture an amount larger than the original authorization amount. This reason code only applies if you are processing a capture through the API.',
    '236' : 'Processor Failure',
    '238' : 'The authorization has already been captured. This reason code only applies if you are processing a capture through the API.',
    '239' : 'The requested transaction amount must match the previous transaction amount. This reason code only applies if you are processing a capture or credit through the API.',
    '240' : 'The card type sent is invalid or does not correlate with the credit card number.',
    '241' : 'The request ID is invalid. This reason code only applies when you are processing a capture or credit through the API.',
    '242' : 'You requested a capture through the API, but there is no corresponding, unused authorization record. Occurs if there was not a previously successful authorization request or if the previously successful authorization has already been used by another capture request. This reason code only applies when you are processing a capture through the API.',
    '243' : 'The transaction has already been settled or reversed.',
    '246' : 'The capture or credit is not voidable because the capture or credit information has already been submitted to your processor. Or, you requested a void for a type of transaction that cannot be voided. This reason code applies only if you are processing a void through the API.',
    '247' : 'You requested a credit for a capture that was previously voided. This reason code applies only if you are processing a void through the API.',
    '250' : 'Error: The request was received, but there was a timeout at the payment processor.',
    '520' : 'The authorization request was approved by the issuing bank but declined by CyberSource based on your Smart Authorization settings.',
}


class PaymentProcessor(BasePaymentProcessor):
    """
    Cybersource payment processing module
    You must have an account with Cybersource in order to use this module
    
    """
    def __init__(self, settings={}):
        
        working_settings = {
            #This is the address to submit live transactions
            'CONNECTION': 'https://ics2ws.ic3.com/commerce/1.x/transactionProcessor/CyberSourceTransaction_1.26.wsdl',

            #This is the address to submit test transactions
            'CONNECTION_TEST': 'https://ics2wstest.ic3.com/commerce/1.x/transactionProcessor/CyberSourceTransaction_1.26.wsdl',

            'LIVE': False,

            'LABEL': _('This will be passed to the translation utility'),

            'CURRENCY_CODE': 'USD',

            'CREDITCHOICES': (
                (('American Express', 'American Express')),
                (('Visa','Visa')),
                (('Mastercard','Mastercard')),
                #(('Discover','Discover'))
            ),

            #Your Cybersource merchant ID - REQUIRED
            'MERCHANT_ID': "",

            #Your Cybersource transaction key - REQUIRED
            'TRANKEY': "",

            'EXTRA_LOGGING': False
        }
        
        working_settings.update(settings)
        super(PaymentProcessor, self).__init__('cybersource', working_settings)

        self.require_settings('MERCHANT_ID', 'TRANKEY')
        
        self.contents = ''
        if self.is_live():
            self.testflag = 'FALSE'
            self.connection = self.settings['CONNECTION']
        else:
            self.testflag = 'TRUE'
            self.connection = self.settings['CONNECTION_TEST']
            
        self.configuration = {
            'merchantID' : self.settings['MERCHANT_ID'],
            'password' : self.settings['TRANKEY'],
        }

    def prepare_content(self, purchase, amount):
        self.bill_to = {
            'firstName' : purchase.first_name,
            'lastName' : purchase.last_name,
            'street1': purchase.full_bill_street,
            'city': purchase.bill_city,
            'state' : purchase.bill_state,
            'postalCode' : purchase.bill_postal_code,
            'country': purchase.bill_country,
            'email' : purchase.email,
            'phoneNumber' : purchase.phone,
            }
        exp = purchase.credit_card.expirationDate.split('/')
        self.card = {
            'accountNumber' : purchase.credit_card.decryptedCC,
            'expirationMonth' : exp[0],
            'expirationYear' : exp[1],
            'cvNumber' : purchase.credit_card.ccv
            }
        currency = self.settings['CURRENCY_CODE']
        currency = currency.replace("_", "")
        self.purchase_totals = {
            'currency' : currency,
            'grandTotalAmount' : trunc_decimal(amount, 2),
        }

    def capture_payment(self, testing=False, purchase=None, amount=NOTSET):
        """
        Creates and sends XML representation of transaction to Cybersource
        """
        if purchase.remaining == Decimal('0.00'):
            self.log_extra('%s is paid in full, no capture attempted.', purchase)
            self.record_payment(purchase=purchase)
            return ProcessorResult(self.key, True, _("No charge needed, paid in full."))

        self.log_extra('Capturing payment for %s', purchase)

        if amount==NOTSET:
            amount = purchase.remaining

        self.prepare_content(purchase, amount)
        
        invoice = "%s" % purchase.id
        failct = purchase.paymentfailures.count()
        if failct > 0:
            invoice = "%s_%i" % (invoice, failct)
        
        # XML format is very simple, using ElementTree for generation would be overkill
        t = loader.get_template('bursar/gateway/cybersource_gateway/request.xml')
        c = Context({
            'config' : self.configuration,
            'merchantReferenceCode' : invoice,
            'billTo' : self.bill_to,
            'purchaseTotals' : self.purchase_totals,
            'card' : self.card,
        })
        request = t.render(c)
        self.log_extra("Cybersource request: %s", request)
        conn = urllib2.Request(url=self.connection, data=request)
        try:
            f = urllib2.urlopen(conn)
        except urllib2.HTTPError, e:
            # we probably didn't authenticate properly
            # make sure the 'v' in your account number is lowercase
            return ProcessorResult(self.key, False, 'Problem parsing results')

        f = urllib2.urlopen(conn)
        all_results = f.read()
        self.log_extra("Cybersource response: %s", all_results)
        tree = fromstring(all_results)
        parsed_results = tree.getiterator('{urn:schemas-cybersource-com:transaction-data-1.26}reasonCode')
        try:
            reason_code = parsed_results[0].text
        except KeyError:
            return ProcessorResult(self.key, False, 'Problem parsing results')

        response_text = CYBERSOURCE_RESPONSES.get(reason_code, 'Unknown Failure')

        if reason_code == '100':
            self.log_extra('%s successfully charged', purchase)
            payment = self.record_payment(purchase=purchase, amount=amount, 
                transaction_id="", reason_code=reason_code)
            return ProcessorResult(self.key, True, response_text, payment=payment)
        else:
            payment = self.record_failure(purchase=purchase, amount=amount, 
                transaction_id="", reason_code=reason_code, 
                details=response_text)
            
            return ProcessorResult(self.key, False, response_text)
