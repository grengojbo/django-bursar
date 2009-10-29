==============
PayPal Gateway
==============

Enabling the module
-------------------
Add "bursar.gateways.paypal_gateway" to your INSTALLED_APPS.  Configure the settings you need for PayPal in your BURSAR_SETTINGS.

Settings
--------

You can configure any of the following settings::

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

    'ENCRYPT' : False,

    # Path to the public key from PayPal, get this at: 
    # https://www.paypal.com/us/cgi-bin/webscr?cmd=_profile-website-cert'
    'PAYPAL_PUBKEY' : "",

    # Path to your paypal private key
    'PRIVATE_KEY': "",

    # Path to your paypal public key
    'PUBLIC_KEY' : ""
    
    # Your Cert ID, copied from the PayPal website after uploading your public key
    'PUBLIC_CERT_ID' = 'get-from-paypal-website'

Encrypted Forms
---------------

The Bursar PayPal Gateway will automatically encrypt the form if you set "ENCRYPT" to True, and you enter values for the "PAYPAL_PUBKEY", "PRIVATE_KEY", "PUBLIC_KEY", and "PUBLIC_CERT_ID".

Thanks to John Boxall's `Django-Paypal`_ project for the encryption method and for the instructions about how to create a PayPal public key:

1. Encrypted forms require the `M2Crypto` library:

        easy_install M2Crypto

2. Encrypted buttons require certificates. Create a private key:

        openssl genrsa -out paypal.pem 1024

3. Create a public key:

        openssl req -new -key paypal.pem -x509 -days 365 -out pubpaypal.pem

4. Upload your public key to the paypal website (sandbox or live). On the "`Encrypted payment settings`_" section of your profile

5.  Copy your "cert id". It's on the screen where you uploaded your public key.

6. Download PayPal's public certificate from that screen.

7. Edit your `settings.py` to include cert information::

    # settings.py
    BURSAR_SETTINGS = {
        'PAYPAL' : {
            'ENCRYPT': True,
            'PAYPAL_PRIVATE_CERT': '/path/to/paypal.pem',
            'PAYPAL_PUBLIC_CERT': '/path/to/pubpaypal.pem',
            'PAYPAL_CERT': '/path/to/paypal_cert.pem',
            'PAYPAL_CERT_ID': 'copied in step 5',
            # add any or all of the other settings for PayPal here
        }
    }

.. _Django-Paypal: http://github.com/johnboxall/django-paypal
.. _Encrypted payment settings: https://www.paypal.com/us/cgi-bin/webscr?cmd=_profile-website-cert