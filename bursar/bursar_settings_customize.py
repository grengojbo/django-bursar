"""Sample Bursar Settings File.

Customize below.  See each gateway processor module for full settings
possible for each that gateway. The built-in tests expect entries such as 
"gateway_TEST" to set up the needed information for each gateway.

Note that for Satchmo, live settings are maintained in the livesettings system, so the only
settings you need are the "gateway_TEST" entries.
"""
from django.utils.translation import ugettext_lazy as _

BURSAR_SETTINGS = {
    'AUTHORIZENET' : {
        'LIVE' : False,
        'SIMULATE' : False,
        'CREDITCHOICES': (
            (('Visa','Visa')),
            (('Mastercard','Mastercard')),
            (('Discover','Discover')),
            #(('American Express', 'American Express'))
        )
        'CAPTURE' : True,
        'EXTRA_LOGGING' : False,
        'ARB' : False,
        'STORE_NAME' : "", #REQUIRED
        'TRANKEY' : "", #REQUIRED
        'EXTRA_LOGGING' : False,
    },
    'AUTHORIZENET_TEST' : {
        'LIVE' : False,
        'SIMULATE' : False,
        'CREDITCHOICES': (
            (('Visa','Visa')),
            (('Mastercard','Mastercard')),
            (('Discover','Discover')),
            #(('American Express', 'American Express'))
        )
        'CAPTURE' : True,
        'EXTRA_LOGGING' : False,
        'ARB' : False,
        'STORE_NAME' : "", #REQUIRED
        'TRANKEY' : "", #REQUIRED
    },
    'AUTOSUCCESS' : {
         'LIVE': False,
         'LABEL': _('Payment Autosuccess Module'),
         'EXTRA_LOGGING': False,
    },
    'AUTOSUCCESS_TEST' : {
         'LIVE': False,
         'LABEL': _('Payment Autosuccess Module'),
         'EXTRA_LOGGING': False,
    },
    'COD' : {
         'SSL': False,
         'LIVE': False,
         'LABEL': _('Payment COD Module'),
         'EXTRA_LOGGING': False,
    },
    'COD_TEST' : {
         'SSL': False,
         'LIVE': False,
         'LABEL': _('Payment COD Module'),
         'EXTRA_LOGGING': False,
    },
    'CYBERSOURCE' : {
        'LIVE': False,
        'LABEL': _('Credit Card (Cybersource)'),
        'CURRENCY_CODE': 'USD',
        'CREDITCHOICES': (
            (('American Express', 'American Express')),
            (('Visa','Visa')),
            (('Mastercard','Mastercard')),
            #(('Discover','Discover'))
        ),
        'MERCHANT_ID' : "", #Your Cybersource merchant ID - REQUIRED
        'TRANKEY': "", #Your Cybersource transaction key - REQUIRED
        'EXTRA_LOGGING': False
    },
    'CYBERSOURCE_TEST' : {
         'LIVE': False,
         'MERCHANT_ID' : "", #Your Cybersource merchant ID - REQUIRED
         'TRANKEY': "", #Your Cybersource transaction key - REQUIRED
         'EXTRA_LOGGING': False
     },
     'PROTX': {
         'LIVE': False,
         'SIMULATOR': False, # Simulated transaction flag - must be false to accept real payments.
         'SKIP_POST': False, # For testing only, this will skip actually posting to Prot/x servers.  
                             # This is because their servers restrict IPs of posting servers, even for tests.
                             # If you are developing on a desktop, you'll have to enable this.

         'CAPTURE': "PAYMENT" # Should be "PAYMENT" or "DEFERRED", Note that you can only use the latter if
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
     },
     'PROTX_TEST': {
         'LIVE': False,
         'SIMULATOR': False,
         'SKIP_POST': False,
         'CAPTURE': "PAYMENT"
         'CREDITCHOICES': (
                     (('VISA','Visa Credit/Debit')),
                     (('MC','Mastercard')),
                 ),
         'VENDOR': "", # REQUIRED
         'VENDOR_SIMULATOR': "",
         'EXTRA_LOGGING': False,
     }
}