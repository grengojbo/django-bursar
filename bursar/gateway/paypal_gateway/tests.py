# -*- coding: UTF-8 -*-
"""Bursar Dummy Gateway Tests."""
from bursar.gateway.paypal_gateway import processor
from bursar.errors import GatewayError
from bursar.models import Authorization, Payment
from bursar.tests import make_test_purchase
from bursar.bursar_settings import get_bursar_setting
from decimal import Decimal
from django.conf import settings
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.core.urlresolvers import reverse as url
from django.test import TestCase
from django.test.client import Client

SKIP_TESTS = False
NEED_SETTINGS = """Tests for paypal_gateway module require an
PAYPAL_TEST section in settings.BURSAR_SETTINGS.  At a 
minimum, you must specify the LOGIN, TRANKEY, and STORE_NAME."""

class TestGateway(TestCase):
    def setUp(self):
        global SKIP_TESTS
        self.client = Client()
        if not SKIP_TESTS:
            settings = get_bursar_setting('PAYPAL_TEST', default_value=None)
            settings['EXTRA_LOGGING'] = True
            if not settings:
                SKIP_TESTS = True
                raise GatewayError(NEED_SETTINGS)
            self.gateway = processor.PaymentProcessor(settings=settings)
            self.default_payment = {
                'ccv' : '111',
                'card_number' : '4111111111111111',
                'expire_month' : 12,
                'expire_year' : 2012,
                'card_type' : 'visa'
            }

    def tearDown(self):
        pass

    def test_capture(self):
        """Test making a direct payment using PAYPAL."""
        if SKIP_TESTS: return
        purchase = make_test_purchase(sub_total=Decimal('10.00'), payment=self.default_payment)
        self.assertEqual(purchase.total, Decimal('10.00'))
        result = self.gateway.capture_payment(purchase=purchase)
        self.assert_(result.success)
        payment = result.payment
        self.assertEqual(payment.amount, Decimal('10.00'))
        self.assertEqual(purchase.total_payments, Decimal('10.00'))
        self.assertEqual(purchase.authorized_remaining, Decimal('0.00'))

