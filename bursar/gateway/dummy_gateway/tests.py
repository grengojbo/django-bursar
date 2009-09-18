# -*- coding: UTF-8 -*-
from bursar.models import Authorization, Payment
from decimal import Decimal
from django.conf import settings
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.core.urlresolvers import reverse as url
from django.test import TestCase
from django.test.client import Client
from bursar.tests import make_test_purchase

class TestGateway(TestCase):
    def setUp(self):
        self.client = Client()

    def tearDown(self):
        pass

    def test_authorize(self):
        """Test making an authorization using DUMMY."""
        purchase = make_test_purchase(sub_total=Decimal('10.00'))
        self.assertEqual(purchase.total, Decimal('10.00'))
    #     self.assertEqual(order.total, Decimal('125.00'))
    # 
    #     processor = utils.get_processor_by_key('PAYMENT_DUMMY')
    #     purchase=order.get_or_create_purchase()
    #     print "PURCHASE=%s" % purchase
    #     processor.create_pending_payment(purchase=purchase, amount=order.total)
    # 
    #     self.assertEqual(purchase.paymentspending.count(), 1)
    # 
    #     pending = purchase.paymentspending.all()[0]
    #     self.assertEqual(pending.amount, order.total)
    # 
    #     payment = purchase.payments.all()[0]
    #     self.assertEqual(payment.amount, Decimal('0'))
    # 
    #     self.assertEqual(pending.capture, payment)
    # 
    #     self.assertEqual(order.balance_paid, Decimal('0'))
    #     self.assertEqual(order.authorized_remaining, Decimal('0'))
    # 
    #     processor.prepare_data(purchase)
    #     result = processor.authorize_payment()
    #     self.assertEqual(result.success, True)
    #     auth = result.payment
    #     self.assertEqual(type(auth), Authorization)
    # 
    #     self.assertEqual(order.authorized_remaining, Decimal('125.00'))
    # 
    #     result = processor.capture_authorized_payment(auth)
    #     self.assertEqual(result.success, True)
    #     payment = result.payment
    #     self.assertEqual(auth.capture, payment)
    #     order = Order.objects.get(pk=order.id)
    #     self.assertEqual(order.balance_paid, Decimal('125.00'))
    #     self.assertEqual(order.status, 'New')
    #     self.assertEqual(order.balance, Decimal('0'))
    # 
    # def test_authorize_multiple(self):
    #     """Test making multiple authorization using DUMMY."""
    #     order = make_test_order(self.US, '')
    #     self.assertEqual(order.balance, order.total)
    #     self.assertEqual(order.total, Decimal('125.00'))
    # 
    #     processor = utils.get_processor_by_key('PAYMENT_DUMMY')
    #     purchase=order.get_or_create_purchase()
    #     processor.create_pending_payment(purchase=purchase, amount=Decimal('25.00'))
    # 
    #     self.assertEqual(order.purchase.paymentspending.count(), 1)
    # 
    #     pending = order.purchase.paymentspending.all()[0]
    # 
    #     self.assertEqual(pending.amount, Decimal('25.00'))
    #     processor.prepare_data(order.purchase)
    #     result = processor.authorize_payment()
    #     self.assertEqual(result.success, True)
    #     #self.assertEqual(order.authorized_remaining, Decimal('25.00'))
    #     self.assertEqual(order.balance, Decimal('100.00'))
    # 
    #     processor.create_pending_payment(purchase=purchase, amount=Decimal('100.00'))
    #     result = processor.authorize_payment()
    # 
    #     results = processor.capture_authorized_payments()
    #     self.assertEqual(len(results), 2)
    # 
    #     r1 = results[0]
    #     r2 = results[1]
    #     self.assertEqual(r1.success, True)
    #     self.assertEqual(r2.success, True)
    #     order = Order.objects.get(pk=order.id)
    #     self.assertEqual(order.status, 'New')
    #     self.assertEqual(order.balance, Decimal('0'))
    # 
    # def test_capture(self):
    #     """Test making a capture without authorization using DUMMY."""
    #     order = make_test_order(self.US, '')
    #     self.assertEqual(order.balance, order.total)
    #     self.assertEqual(order.total, Decimal('125.00'))
    # 
    #     processor = utils.get_processor_by_key('PAYMENT_DUMMY')
    #     purchase=order.get_or_create_purchase()
    #     processor.create_pending_payment(purchase=purchase, amount=order.total)
    # 
    #     processor.prepare_data(order.purchase)
    #     result = processor.capture_payment()
    #     self.assertEqual(result.success, True)
    #     pmt1 = result.payment
    #     self.assertEqual(type(pmt1), Payment)
    # 
    #     self.assertEqual(order.authorized_remaining, Decimal('0.00'))
    # 
    #     self.assertEqual(result.success, True)
    #     payment = result.payment
    #     self.assertEqual(pmt1, payment)
    #     order = Order.objects.get(pk=order.id)
    #     self.assertEqual(order.status, 'New')
    #     self.assertEqual(order.balance, Decimal('0'))
    # 
    # 
    # 
    # def test_multiple_pending(self):
    #     """Test that creating a second pending payment deletes the first one."""
    #     order = make_test_order(self.US, '')
    #     self.assertEqual(order.balance, order.total)
    #     self.assertEqual(order.total, Decimal('125.00'))
    # 
    #     processor = utils.get_processor_by_key('PAYMENT_DUMMY')
    #     purchase=order.get_or_create_purchase()
    #     pend1 = processor.create_pending_payment(purchase=purchase, amount=order.total)
    #     pend2 = processor.create_pending_payment(purchase=purchase, amount=order.total)
    # 
    #     self.assertEqual(order.purchase.paymentspending.count(), 1)
