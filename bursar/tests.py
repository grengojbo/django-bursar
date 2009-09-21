# -*- coding: UTF-8 -*-
from bursar.models import Authorization, Payment, Purchase, CreditCardDetail
from decimal import Decimal
from django.conf import settings
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.core.urlresolvers import reverse as url
from django.test import TestCase
from django.test.client import Client
import random

alphabet = 'abcdefghijklmnopqrstuvwxyz'

def make_test_purchase(payment={}, **kwargs):
    purchaseargs = {
        "first_name": 'Mister',
        "last_name": 'Tester',
        "orderno" : "test%03i" % random.randrange(1,100),
        "email" : "test@example.com",
        "phone" : "555-555-1234",
        "ship_street1" : "123 Test St.",
        "ship_city" : "Testington",
        "ship_state" : "TX",
        "ship_postal_code" : "55555",
        "ship_country" : "US",
        "bill_street1" : "123 Test St.",
        "bill_city" : "Testington",
        "bill_state" : "TX",
        "bill_postal_code" : "55555",
        "bill_country" : "US",
        "tax" : Decimal("0"),
        "shipping" : Decimal("0"),
    }
    purchaseargs.update(kwargs)
    purchase = Purchase(**purchaseargs)
    purchase.recalc()
    purchase.save()
    if payment:
        for f in ('card_type', 'expire_month', 'expire_year', 'card_number', 'ccv'):
            assert(f in payment)
        p = Payment(purchase = purchase, amount = purchase.total)
        p.save()
        c = CreditCardDetail(
            payment=p, 
            credit_type=payment['card_type'],
            expire_month=payment['expire_month'],
            expire_year=payment['expire_year'],
        )
        c.storeCC(payment['card_number'])
        c.ccv = payment['ccv']
        c.save()        
        
    return purchase

class TestBase(TestCase):
    def setUp(self):
        self.client = Client()

    def tearDown(self):
        pass

    def test_authorize(self):
        """Test making an authorization using DUMMY."""
        purchase = make_test_purchase(sub_total=Decimal('10.00'))
        self.assertEqual(purchase.total, Decimal('10.00'))