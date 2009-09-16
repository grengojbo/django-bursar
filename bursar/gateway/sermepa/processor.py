from bursar.gateway.base import HeadlessPaymentProcessor

class PaymentProcessor(HeadlessPaymentProcessor):

    def __init__(self, settings):
        super(PaymentProcessor, self).__init__('sermepa', settings)
