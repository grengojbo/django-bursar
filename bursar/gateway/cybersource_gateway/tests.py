# -*- coding: UTF-8 -*-
"""Bursar Authorizenet Gateway Tests."""
from bursar.gateway.cybersource_gateway import processor
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
NEED_SETTINGS = """Tests for cybersource_gateway module require a
CYBERSOURCE_TEST section in settings.BURSAR_SETTINGS.  At a 
minimum, you must specify the 'MERCHANT_ID' and 'TRANKEY'."""

class TestGateway(TestCase):
    def setUp(self):
        global SKIP_TESTS
        self.client = Client()
        if not SKIP_TESTS:
            settings = get_bursar_setting('CYBERSOURCE_TEST', default_value=None)
            if not settings:
                SKIP_TESTS = True
                raise GatewayError(NEED_SETTINGS)
            settings['EXTRA_LOGGING'] = True
            self.gateway = processor.PaymentProcessor(settings=settings)
            self.default_payment = {
                'ccv' : '144',
                'card_number' : '6011000000000012',
                'expire_month' : 12,
                'expire_year' : 2012,
                'card_type' : 'visa'
            }

    def tearDown(self):
        pass
        
    # def test_authorize(self):
    #     if SKIP_TESTS: return
    #     purchase = make_test_purchase(sub_total=Decimal('20.00'), payment=self.default_payment)
    #     result = self.gateway.authorize_payment(purchase=purchase)
    #     self.assert_(result.success)
    #     payment = result.payment
    #     self.assertEqual(payment.amount, Decimal('20.00'))
    #     self.assertEqual(purchase.total_payments, Decimal('0.00'))
    #     self.assertEqual(purchase.authorized_remaining, Decimal('20.00'))

    # def test_pending_authorize(self):
    #     if SKIP_TESTS: return
    #     purchase = make_test_purchase(sub_total=Decimal('20.00'), payment=self.default_payment)
    #     self.assert_(purchase.credit_card)
    #     pending = self.gateway.create_pending_payment(purchase)
    #     self.assertEqual(pending.amount, Decimal('20.00'))
    #     result = self.gateway.authorize_payment(purchase=purchase)
    #     self.assert_(result.success)
    #     payment = result.payment
    #     self.assertEqual(payment.amount, Decimal('20.00'))
    #     self.assertEqual(purchase.total_payments, Decimal('0.00'))
    #     self.assertEqual(purchase.authorized_remaining, Decimal('20.00'))

    def test_capture(self):
        """Test making a direct payment using CYBERSOURCE."""
        if SKIP_TESTS: return
        purchase = make_test_purchase(sub_total=Decimal('10.00'), payment=self.default_payment)
        self.assertEqual(purchase.total, Decimal('10.00'))
        result = self.gateway.capture_payment(purchase=purchase)
        self.assert_(result.success)
        payment = result.payment
        self.assertEqual(payment.amount, Decimal('10.00'))
        self.assertEqual(purchase.total_payments, Decimal('10.00'))
        self.assertEqual(purchase.authorized_remaining, Decimal('0.00'))

    # def test_authorize_multiple(self):
    #     """Test making multiple authorization using CYBERSOURCE."""
    #     if SKIP_TESTS: return
    #     purchase = make_test_purchase(sub_total=Decimal('100.00'), payment=self.default_payment)
    #     self.assertEqual(purchase.total, Decimal('100.00'))
    #     pending = self.gateway.create_pending_payment(purchase=purchase, amount=Decimal('25.00'))
    #     self.assertEqual(pending.amount, Decimal('25.00'))
    #     self.assertEqual(purchase.paymentspending.count(), 1)
    #     pending2 = purchase.get_pending(self.gateway.key)
    #     self.assertEqual(pending, pending2)
    #     result = self.gateway.authorize_payment(purchase)
    #     self.assertEqual(result.success, True)
    #     self.assertEqual(purchase.authorized_remaining, Decimal('25.00'))
    #     self.assertEqual(purchase.remaining, Decimal('75.00'))
    # 
    #     self.gateway.create_pending_payment(purchase=purchase, amount=Decimal('75.00'))
    #     result = self.gateway.authorize_payment(purchase)
    #     self.assert_(result.success)
    #     auth = result.payment
    #     self.assertEqual(auth.amount, Decimal('75.00'))
    #     self.assertEqual(purchase.authorized_remaining, Decimal('100.00'))
    # 
    #     results = self.gateway.capture_authorized_payments(purchase)
    #     self.assertEqual(len(results), 2)
    #     r1 = results[0]
    #     r2 = results[1]
    #     self.assertEqual(r1.success, True)
    #     self.assertEqual(r2.success, True)
    #     self.assertEqual(purchase.total_payments, Decimal('100'))

    def test_multiple_pending(self):
        """Test that creating a second pending payment deletes the first one."""
        if SKIP_TESTS: return
        purchase = make_test_purchase(sub_total=Decimal('125.00'), payment=self.default_payment)
        self.assertEqual(purchase.total, Decimal('125.00'))
        pend1 = self.gateway.create_pending_payment(purchase=purchase, amount=purchase.total)
        pend2 = self.gateway.create_pending_payment(purchase=purchase, amount=purchase.total)
    
        self.assertEqual(purchase.paymentspending.count(), 1)
