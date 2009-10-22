"""Prot/X Payment Gateway.
"""
from bursar.gateway.base import BasePaymentProcessor, ProcessorResult, NOTSET
from bursar.errors import GatewayError
from bursar.numbers import trunc_decimal
from decimal import Decimal
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
import urllib2

PROTOCOL = "2.22"

class PaymentProcessor(BasePaymentProcessor):
    packet = {}
    response = {}
    
    def __init__(self, settings={}):
        
        working_settings = {
            'LIVE_CONNECTION' : 'https://ukvps.protx.com/vspgateway/service/vspdirect-register.vsp',
            'LIVE_CALLBACK' : 'https://ukvps.protx.com/vspgateway/service/direct3dcallback.vsp',
            'TEST_CONNECTION' : 'https://ukvpstest.protx.com/vspgateway/service/vspdirect-register.vsp',
            'TEST_CALLBACK' : 'https://ukvpstest.protx.com/vspgateway/service/direct3dcallback.vsp',
            'SIMULATOR_CONNECTION' : 'https://ukvpstest.protx.com/VSPSimulator/VSPDirectGateway.asp',
            'SIMULATOR_CALLBACK' : 'https://ukvpstest.protx.com/VSPSimulator/VSPDirectCallback.asp',
            
            'LIVE': False,
            'SIMULATOR': False, # Simulated transaction flag - must be false to accept real payments.
            'SKIP_POST': False, # For testing only, this will skip actually posting to Prot/x servers.  
                                # This is because their servers restrict IPs of posting servers, even for tests.
                                # If you are developing on a desktop, you'll have to enable this.

            'CAPTURE': "PAYMENT", # Should be "PAYMENT" or "DEFERRED", Note that you can only use the latter if
                                  # you set that option on your Prot/X account first.
            'LABEL': _('Prot/X Secure Payments'),
            'CREDITCHOICES': (
                        (('VISA','Visa Credit/Debit')),
                        #(('UKE','Visa Electron')),
                        #(('DELTA','Delta')),
                        #(('AMEX','American Express')),  # not always available
                        #(('DC','Diners Club')), # not always available
                        (('MC','Mastercard')),
                        #(('MAESTRO','UK Maestro')),
                        #(('SOLO','Solo')),
                        #(('JCB','JCB')),
                    ),

            'VENDOR': "", # REQUIRED, your vendor name. This is used for Live and Test transactions.  
                         # Make sure to add your server IP address to VSP, or it won't work.

            'VENDOR_SIMULATOR': "", # Simulator Vendor Name
                                   # This is used for Live and Test transactions.  Make sure to activate
                                   # the VSP Simulator (you have to directly request it) and add your
                                   # server IP address to the VSP Simulator, or it won't work.")),

            'CURRENCY_CODE': 'GBP',

            'EXTRA_LOGGING': False,
        }
        working_settings.update(settings)            
        super(PaymentProcessor, self).__init__('protx', working_settings)
        self.require_settings('VENDOR')

        if self.settings['SIMULATOR']:
            try:
                self.require_settings('VENDOR_SIMULATOR')
            except GatewayError, ge:
                self.log.warn("You are trying to use the Prot/X VSP Simulator, but you don't have a vendor name in settings for the simulator.")
                raise ge
                
            vendor = self.settings['VENDOR_SIMULATOR']
        else:
            vendor = self.settings['VENDOR']
        
        self.packet = {
            'VPSProtocol': PROTOCOL,
            'TxType': self.settings['CAPTURE'],
            'Vendor': vendor,
            'Currency': self.settings['CURRENCY_CODE'],
            }
        self.valid = False

    def _url(self, key):
        if self.settings['SIMULATOR']:
            key = "SIMULATOR_" + key
        else:
            if self.is_live():
                key = "LIVE_" + key
            else:
                key = "TEST_" + key
        return self.settings[key]

    @property
    def connection(self):
        return self._url('CONNECTION')
        
    @property
    def callback(self):
        return self._url('CALLBACK')
        
    def prepare_post(self, purchase, amount):
        
        invoice = "%s" % purchase.id
        failct = purchase.paymentfailures.count()
        if failct > 0:
            invoice = "%s_%i" % (invoice, failct)
        
        try:
            cc = purchase.credit_card
            balance = trunc_decimal(purchase.remaining, 2)
            self.packet['VendorTxCode'] = invoice
            self.packet['Amount'] = balance
            self.packet['Description'] = 'Online purchase'
            self.packet['CardType'] = cc.credit_type
            self.packet['CardHolder'] = cc.card_holder
            self.packet['CardNumber'] = cc.decryptedCC
            self.packet['ExpiryDate'] = '%02d%s' % (cc.expire_month, str(cc.expire_year)[2:])
            if cc.start_month is not None:
                self.packet['StartDate'] = '%02d%s' % (cc.start_month, str(cc.start_year)[2:])
            if cc.ccv is not None and cc.ccv != "":
                self.packet['CV2'] = cc.ccv
            if cc.issue_num is not None and cc.issue_num != "":
                self.packet['IssueNumber'] = cc.issue_num #'%02d' % int(cc.issue_num)
            addr = [purchase.bill_street1, purchase.bill_street2, purchase.bill_city, purchase.bill_state]
            self.packet['BillingAddress'] = ', '.join(addr)
            self.packet['BillingPostCode'] = purchase.bill_postal_code
        except Exception, e:
            self.log.error('preparing data, got error: %s\nData: %s', e, purchase)
            self.valid = False
            return
            
        # handle pesky unicode chars in names
        for key, value in self.packet.items():
            try:
                value = value.encode('utf-8')
                self.packet[key] = value
            except AttributeError:
                pass
        
        self.postString = urlencode(self.packet)
        self.url = self.connection
        self.valid = True
    
    def prepare_data3d(self, md, pares):
        self.packet = {}
        self.packet['MD'] = md
        self.packet['PARes'] = pares
        self.postString = urlencode(self.packet)
        self.url = self.callback
        self.valid = True
        
    def capture_payment(self, testing=False, purchase=None, amount=NOTSET):
        """Execute the post to protx VSP DIRECT"""
        if not purchase:
            purchase = self.purchase

        if purchase.remaining == Decimal('0.00'):
            self.log_extra('%s is paid in full, no capture attempted.', purchase)
            self.record_payment(purchase=purchase)
            return ProcessorResult(self.key, True, _("No charge needed, paid in full."))

        self.log_extra('Capturing payment for %s', purchase)

        if amount == NOTSET:
            amount = purchase.remaining

        self.prepare_post(purchase, amount)
        
        if self.valid:
            if self.settings['SKIP_POST']:
                self.log.info("TESTING MODE - Skipping post to server.  Would have posted %s?%s", self.url, self.postString)
                payment = self.record_payment(purchase=purchase, amount=amount, 
                    transaction_id="TESTING", reason_code='0')

                return ProcessorResult(self.key, True, _('TESTING MODE'), payment=payment)
                
            else:
                self.log_extra("About to post to server: %s?%s", self.url, self.postString)
                conn = urllib2.Request(self.url, data=self.postString)
                try:
                    f = urllib2.urlopen(conn)
                    result = f.read()
                    self.log_extra('Process: url=%s\nPacket=%s\nResult=%s', self.url, self.packet, result)

                except urllib2.URLError, ue:
                    self.log.error("error opening %s\n%s", self.url, ue)
                    return ProcessorResult(self.key, False, 'ERROR: Could not talk to Protx gateway')

                try:
                    self.response = dict([row.split('=', 1) for row in result.splitlines()])
                    status = self.response['Status']
                    success = (status == 'OK')
                    detail = self.response['StatusDetail']
                
                    payment = None
                    transaction_id = ""
                    if success:
                        vpstxid = self.response.get('VPSTxID', '')
                        txauthno = self.response.get('TxAuthNo', '')
                        transaction_id="%s,%s" % (vpstxid, txauthno)
                        self.log.info('Success on purchase #%i, recording payment', self.purchase.id)
                        payment = self.record_payment(purchase=purchase, amount=amount, 
                            transaction_id=transaction_id, reason_code=status)
                        
                    else:
                        payment = self.record_failure(purchase=purchase, amount=amount, 
                            transaction_id=transaction_id, reason_code=status, 
                            details=detail)

                    return ProcessorResult(self.key, success, detail, payment=payment)

                except Exception, e:
                    self.log.info('Error submitting payment: %s', e)
                    payment = self.record_failure(purchase=purchase, amount=amount, 
                        transaction_id="", reason_code="error", 
                        details='Invalid response from bursar gateway')
                    
                    return ProcessorResult(self.key, False, _('Invalid response from bursar gateway'))
        else:
            return ProcessorResult(self.key, False, _('Error processing payment.'))
