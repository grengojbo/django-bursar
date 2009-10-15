from bursar.errors import GatewayError
from bursar.gateway.base import HeadlessPaymentProcessor
from django.utils.translation import ugettext as _

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
        if working_settings['LIVE']:
            for key in ("POST_URL", "BUSINESS"):
                if not key in working_settings and working_settings[key]:
                    raise GatewayError('Paypal processor needs a %s in its settings.' % key)
        else:
            for key in ("POST_TEST_URL", "BUSINESS_TEST"):
                if not key in working_settings and working_settings[key]:
                    raise GatewayError('Paypal processor needs a %s in its settings.' % key)

        super(PaymentProcessor, self).__init__('paypal', working_settings)
