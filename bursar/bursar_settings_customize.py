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
}