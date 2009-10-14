from bursar.gateway.base import HeadlessPaymentProcessor

class PaymentProcessor(HeadlessPaymentProcessor):

    def __init__(self, settings={}):
        working_settings = {
            'SSL' : False,
            'LIVE' : False,
            'LABEL' : _('PayPal'),
            'URL_BASE': r'^paypal/',
            'CAPTURE' : True,
            'EXTRA_LOGGING' : False,
            }
        working_settings.update(settings)
        if not 'LOGIN' in working_settings:
            raise GatewayError('You must define a LOGIN for the PAYPAL payment module.')

        if not 'STORE_NAME' in working_settings:
            raise GatewayError('You must define a STORE_NAME for the PAYPAL payment module.')

        if not 'TRANKEY' in working_settings:
            raise GatewayError('You must provide a TRANKEY for the PAYPAL payment module.')
            
        super(PaymentProcessor, self).__init__('paypal', working_settings)
