# -*- coding: UTF-8 -*-
from payment import utils
from decimal import Decimal
from django.conf import settings
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.core.urlresolvers import reverse as url
from django.test import TestCase
from django.test.client import Client
from django.test.client import Client
from l10n.models import *
from livesettings import config_get_group, config_value, config_get
from payment.tests import make_test_order
from product.models import *
from satchmo_store.contact.models import *
from satchmo_store.shop.models import *
from satchmo_utils.dynamic import lookup_template, lookup_url
import keyedcache

alphabet = 'abcdefghijklmnopqrstuvwxyz'

class TestGateway(TestCase):
    fixtures = ['l10n-data.yaml', 'sample-store-data.yaml', 'products.yaml', 'test-config.yaml']

    def setUp(self):
        self.client = Client()
        self.US = Country.objects.get(iso2_code__iexact = "US")

    def tearDown(self):
        keyedcache.cache_delete()

    def test_authorize(self):
        """Test making an authorization using DUMMY."""
        order = make_test_order(self.US, '')
        self.assertEqual(order.balance, order.total)
        self.assertEqual(order.total, Decimal('125.00'))

        processor = utils.get_processor_by_key('PAYMENT_DUMMY')
        processor.create_pending_payment(order=order, amount=order.total)

        self.assertEqual(order.paymentspending.count(), 1)
        self.assertEqual(order.purchases.count(), 1)

        pending = order.paymentspending.all()[0]
        self.assertEqual(pending.amount, order.total)

        payment = order.purchases.all()[0]
        self.assertEqual(payment.amount, Decimal('0'))

        self.assertEqual(pending.capture, payment)

        self.assertEqual(order.balance_paid, Decimal('0'))
        self.assertEqual(order.authorized_remaining, Decimal('0'))

        processor.prepare_data(order)
        result = processor.authorize_payment()
        self.assertEqual(result.success, True)
        auth = result.payment
        self.assertEqual(type(auth), OrderAuthorization)

        self.assertEqual(order.authorized_remaining, Decimal('125.00'))

        result = processor.capture_authorized_payment(auth)
        self.assertEqual(result.success, True)
        payment = result.payment
        self.assertEqual(auth.capture, payment)
        order = Order.objects.get(pk=order.id)
        self.assertEqual(order.status, 'New')
        self.assertEqual(order.balance, Decimal('0'))

    def test_authorize_multiple(self):
        """Test making multiple authorization using DUMMY."""
        order = make_test_order(self.US, '')
        self.assertEqual(order.balance, order.total)
        self.assertEqual(order.total, Decimal('125.00'))

        processor = utils.get_processor_by_key('PAYMENT_DUMMY')
        processor.create_pending_payment(order=order, amount=Decimal('25.00'))

        self.assertEqual(order.paymentspending.count(), 1)
        self.assertEqual(order.purchases.count(), 1)

        pending = order.paymentspending.all()[0]

        self.assertEqual(pending.amount, Decimal('25.00'))
        processor.prepare_data(order)
        result = processor.authorize_payment()
        self.assertEqual(result.success, True)
        #self.assertEqual(order.authorized_remaining, Decimal('25.00'))
        #self.assertEqual(order.balance, Decimal('100.00'))

        processor.create_pending_payment(order=order, amount=Decimal('100.00'))
        result = processor.authorize_payment()

        results = processor.capture_authorized_payments()
        self.assertEqual(len(results), 2)

        r1 = results[0]
        r2 = results[1]
        self.assertEqual(r1.success, True)
        self.assertEqual(r2.success, True)
        order = Order.objects.get(pk=order.id)
        self.assertEqual(order.status, 'New')
        self.assertEqual(order.balance, Decimal('0'))

    def test_capture(self):
        """Test making a capture without authorization using DUMMY."""
        order = make_test_order(self.US, '')
        self.assertEqual(order.balance, order.total)
        self.assertEqual(order.total, Decimal('125.00'))

        processor = utils.get_processor_by_key('PAYMENT_DUMMY')
        processor.create_pending_payment(order=order, amount=order.total)

        processor.prepare_data(order)
        result = processor.capture_payment()
        self.assertEqual(result.success, True)
        pmt1 = result.payment
        self.assertEqual(type(pmt1), OrderPayment)

        self.assertEqual(order.authorized_remaining, Decimal('0.00'))

        self.assertEqual(result.success, True)
        payment = result.payment
        self.assertEqual(pmt1, payment)
        order = Order.objects.get(pk=order.id)
        self.assertEqual(order.status, 'New')
        self.assertEqual(order.balance, Decimal('0'))



    def test_multiple_pending(self):
        """Test that creating a second pending payment deletes the first one."""
        order = make_test_order(self.US, '')
        self.assertEqual(order.balance, order.total)
        self.assertEqual(order.total, Decimal('125.00'))

        processor = utils.get_processor_by_key('PAYMENT_DUMMY')
        pend1 = processor.create_pending_payment(order=order, amount=order.total)
        pend2 = processor.create_pending_payment(order=order, amount=order.total)

        self.assertEqual(order.paymentspending.count(), 1)
        self.assertEqual(order.purchases.count(), 1)