"""
Stores details about the available payment options.
Also stores credit card info in an encrypted format.
"""

from bursar.fields import PaymentChoiceCharField, CreditChoiceCharField, CurrencyField
from Crypto.Cipher import Blowfish
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from livesettings import config_value
import base64
import keyedcache
import logging
import operator

log = logging.getLogger('bursar.models')

# ----------------------
# Abstract Base Models
# ----------------------

class PaymentBase(models.Model):
    method = PaymentChoiceCharField(_("Payment Method"),
        max_length=25, blank=True)
    amount = CurrencyField(_("amount"), 
        max_digits=18, decimal_places=2, blank=True, null=True)
    time_stamp = models.DateTimeField(_("timestamp"), blank=True, null=True)
    transaction_id = models.CharField(_("Transaction ID"), max_length=45, blank=True, null=True)
    details = models.CharField(_("Details"), max_length=255, blank=True, null=True)
    reason_code = models.CharField(_('Reason Code'),  max_length=255, blank=True, null=True)

    def _credit_card(self):
        """Return the credit card associated with this payment."""
        try:
            return self.creditcards.get()
        except self.creditcards.model.DoesNotExist:
            return None
    credit_card = property(_credit_card)

    def save(self, force_insert=False, force_update=False):
        if not self.pk:
            self.time_stamp = datetime.now()

        super(PaymentBase, self).save(force_insert=force_insert, force_update=force_update)

    class Meta:
        abstract = True

# --------------------
# Concrete models
# --------------------

class Authorization(PaymentBase):
    """
    An AUTH received from a credit card gateway.
    """
    purchase = models.ForeignKey('Purchase', related_name="authorizations")
    capture = models.ForeignKey('Payment', related_name="authorizations")
    complete = models.BooleanField(_('Complete'), default=False)

    def __unicode__(self):
        if self.id is not None:
            return u"Order Authorization #%i" % self.id
        else:
            return u"Order Authorization (unsaved)"

    def remaining(self):
        payments = [p.amount for p in self.purchase.payments.all()]
        if payments:
            amount = reduce(operator.add, payments)
        else:
            amount = Decimal('0.00')
        
        remaining = self.order.total - amount
        if remaining > self.amount:
            remaining = self.amount
            
    def save(self, force_insert=False, force_update=False):
        # create linked payment
        try:
            capture = self.capture
        except Payment.DoesNotExist:
            log.debug('Payment Authorization - creating linked payment')
            log.debug('order is: %s', self.order)
            self.capture = Payment.objects.create_linked(self)
        super(PaymentBase, self).save(force_insert=force_insert, force_update=force_update)

    class Meta:
        verbose_name = _("Order Payment Authorization")
        verbose_name_plural = _("Order Payment Authorizations")
            
class CreditCardDetail(models.Model):
    """
    Stores an encrypted CC number, its information, and its
    displayable number.
    """
    payment = models.ForeignKey('Payment', related_name="creditcards")
    credit_type = CreditChoiceCharField(_("Credit Card Type"), max_length=16)
    display_cc = models.CharField(_("CC Number (Last 4 digits)"),
        max_length=4, )
    encrypted_cc = models.CharField(_("Encrypted Credit Card"),
        max_length=40, blank=True, null=True, editable=False)
    expire_month = models.IntegerField(_("Expiration Month"))
    expire_year = models.IntegerField(_("Expiration Year"))
    card_holder = models.CharField(_("card_holder Name"), max_length=60, blank=True)
    start_month = models.IntegerField(_("Start Month"), blank=True, null=True)
    start_year = models.IntegerField(_("Start Year"), blank=True, null=True)
    issue_num = models.CharField(blank=True, null=True, max_length=2)
    
    def storeCC(self, ccnum):
        """
        Take as input a valid cc, encrypt it and store the last 4 digits in a visible form
        """
        self.display_cc = ccnum[-4:]
        encrypted_cc = _encrypt_code(ccnum)
        if config_value('GATEWAY', 'STORE_CREDIT_NUMBERS'):
            self.encrypted_cc = encrypted_cc
        else:
            standin = "%s%i%i%i" % (self.display_cc, self.expire_month, self.expire_year, self.payment_id)
            self.encrypted_cc = _encrypt_code(standin)
            key = _encrypt_code(standin + '-card')
            keyedcache.cache_set(key, skiplog=True, length=60*60, value=encrypted_cc)
    
    def setCCV(self, ccv):
        """
        Put the CCV in the cache, don't save it for security/legal reasons.
        """
        if not self.encrypted_cc:
            raise ValueError('CreditCardDetail expecting a credit card number to be stored before storing CCV')
            
        keyedcache.cache_set(self.encrypted_cc, skiplog=True, length=60*60, value=ccv)
    
    def getCCV(self):
        """Get the CCV from cache"""
        try:
            ccv = keyedcache.cache_get(self.encrypted_cc)
        except keyedcache.NotCachedError:
            ccv = ""

        return ccv
    
    ccv = property(fget=getCCV, fset=setCCV)
    
    def _decryptCC(self):
        ccnum = _decrypt_code(self.encrypted_cc)
        if not config_value('GATEWAY', 'STORE_CREDIT_NUMBERS'):
            try:
                key = _encrypt_code(ccnum + '-card')
                encrypted_ccnum = keyedcache.cache_get(key)
                ccnum = _decrypt_code(encrypted_ccnum)
            except keyedcache.NotCachedError:
                ccnum = ""
        return ccnum
                
    decryptedCC = property(_decryptCC) 

    def _expireDate(self):
        return(str(self.expire_month) + "/" + str(self.expire_year))
    expirationDate = property(_expireDate)
    
    class Meta:
        verbose_name = _("Credit Card")
        verbose_name_plural = _("Credit Cards")

class PaymentManager(models.Manager):
    def create_linked(self, other):
        linked = Payment(
                purchase = other.purchase,
                method = other.method,
                amount=Decimal('0.00'),
                transaction_id="LINKED",
                details=other.details,
                reason_code="")
        linked.save()
        return linked

class Payment(PaymentBase):
    """
    A payment attempt on a purchase.
    """
    purchase = models.ForeignKey('Purchase', related_name="payments")
    objects = PaymentManager()

    def __unicode__(self):
        if self.id is not None:
            return u"Order Payment #%i" % self.id
        else:
            return u"Order Payment (unsaved)"

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")


class PaymentFailure(PaymentBase):
    """
    Details of a failure during a payment attempt
    """
    purchase = models.ForeignKey('Purchase', null=True, blank=True, related_name='paymentfailures')

class PaymentPending(PaymentBase):
    """
    Associates a payment with an Authorization.
    """
    purchase = models.ForeignKey('Purchase', related_name="paymentspending")
    capture = models.ForeignKey(Payment, related_name="paymentspending")
    
    def __unicode__(self):
        if self.id is not None:
            return u"Pending Payment #%i" % self.id
        else:
            return u"Pending Payment (unsaved)"

    def save(self, force_insert=False, force_update=False):
        # create linked payment
        try:
            capture = self.capture
        except Payment.DoesNotExist:
            log.debug('Pending Payment - creating linked payment')
            self.capture = Payment.objects.create_linked(self)
        super(PaymentBase, self).save(force_insert=force_insert, force_update=force_update)

    class Meta:
        verbose_name = _("Pending Payment")
        verbose_name_plural = _("Pending Payments")


class PurchaseManager(models.Manager):
    pass

class Purchase(models.Model):
    """
    Collects information about an order and tracks
    its state.
    """
    orderno = models.CharField(_("Order Number"), max_length=20)
    first_name = models.CharField(_("First name"), max_length=30)
    last_name = models.CharField(_("Last name"), max_length=30)
    email = models.EmailField(_("Email"), max_length=75, default="")
    phone = models.CharField(_("Phone Number"), max_length=30, default="")
    ship_street1 = models.CharField(_("Street"), max_length=80, default="")
    ship_street2 = models.CharField(_("Street"), max_length=80, default="")
    ship_city = models.CharField(_("City"), max_length=50, default="")
    ship_state = models.CharField(_("State"), max_length=50, default="")
    ship_postal_code = models.CharField(_("Zip Code"), max_length=30, default="")
    ship_country = models.CharField(_("Country"), max_length=2, default="")
    bill_addressee = models.CharField(_("Addressee"), max_length=61, default="")
    bill_street1 = models.CharField(_("Street"), max_length=80, default="")
    bill_street2 = models.CharField(_("Street"), max_length=80, default="")
    bill_city = models.CharField(_("City"), max_length=50, default="")
    bill_state = models.CharField(_("State"), max_length=50, default="")
    bill_postal_code = models.CharField(_("Zip Code"), max_length=30, default="")
    bill_country = models.CharField(_("Country"), max_length=2, default="")
    sub_total = CurrencyField(_("Subtotal"), 
        max_digits=18, decimal_places=2, blank=True, null=True, display_decimal=4)
    tax = CurrencyField(_("Tax"),
        max_digits=18, decimal_places=2, blank=True, null=True, display_decimal=4)
    shipping_cost = CurrencyField(_("Shipping Cost"),
        max_digits=18, decimal_places=2, blank=True, null=True, display_decimal=4)
    total = CurrencyField(_("Total"),
        max_digits=18, decimal_places=2, display_decimal=4)
    time_stamp = models.DateTimeField(_("Timestamp"), blank=True, null=True)

    objects = PurchaseManager()

    def __unicode__(self):
        return "Purchase #%s on Order #%s" % (self.id, self.orderno)

    @property
    def authorized_remaining(self):
        """Returns the total value of all un-captured authorizations"""
        auths = [p.amount for p in self.authorizations.filter(complete=False)]
        if auths:
            amount = reduce(operator.add, auths)
        else:
            amount = Decimal('0.00')

        return amount
        
    @property
    def credit_card(self):
        """Return the credit card associated with this payment.
        """
        for payment in self.payments.order_by('-time_stamp'):
            if payment.creditcards.count() > 0:
                return payment.creditcards.get()
        return None

    def recurring_lineitems(self):
        """Get all recurring lineitems"""
        subscriptions = [item for item in self.lineitems.all() if item.is_recurring]
        return subscriptions
    
    def save(self, **kwargs):
        """
        Copy addresses from contact. If the order has just been created, set
        the create_date.
        """
        if not self.pk:
            self.time_stamp = datetime.now()
        super(Purchase, self).save(**kwargs)
        
    @property
    def total_payments(self):
        """Returns the total value of all completed payments"""
        payments = [p.amount for p in self.payments.all()]
        if payments:
            amount = reduce(operator.add, payments)
        else:
            amount = Decimal('0.00')
            
        return amount

        
        
class LineItem(models.Model):
    """A single line item in a purchase.  This is optional, only needed for certain
    gateways such as Google or PayPal."""
    purchase = models.ForeignKey(Purchase, 
        verbose_name=_("Purchase"), related_name="lineitems")
    ordering = models.PositiveIntegerField(_('Ordering'),
        default=0)
    name = models.CharField(_('Item'), max_length=100)
    description = models.TextField(_('Description'), 
        blank=True)
    quantity = models.DecimalField(_("Quantity"),  
        max_digits=18, decimal_places=6,
        default=Decimal('1'))
    unit_price = CurrencyField(_("Unit price"),
        max_digits=18, decimal_places=10)
    subtotal = CurrencyField(_("Line item price"),
        max_digits=18, decimal_places=10)
    shipping_price = CurrencyField(_("Shipping price"),
        max_digits=18, decimal_places=10, 
        default=Decimal('0.00'))
    discount = CurrencyField(_("Line item discount"),
        max_digits=18, decimal_places=10,
        default=Decimal('0.00'))
    tax = CurrencyField(_("Line item tax"),
        max_digits=18, decimal_places=10,
        default=Decimal('0.00'))
    total = CurrencyField(_("Total"),
        max_digits=18, decimal_places=2,
        default=Decimal('0.00'))
    
    class Meta:
        ordering = ('ordering',)
        
    @property
    def is_recurring(self):
        recur = False
        try:
            if self.recurdetails and self.recurdetails is not None:
                recur = True
        except RecurringLineItem.DoesNotExist:
            pass
        
        return recur
        
    def recalc(self):
        """Recalculate totals"""
        self.subtotal = self.quantity * self.unit_price
        self.total = self.subtotal - self.discount + self.tax + self.shipping_price
                
    def __unicode__(self):
        return "LineItem: %s - %d" % (self.name, self.total) 

class RecurringLineItem(models.Model):
    """Extra information needed for a recurring line item, such as a subscription"""
    lineitem = models.OneToOneField(LineItem, verbose_name=_("Line Item"), 
        primary_key=True, related_name="recurdetails")
    recurring = models.BooleanField(_("Recurring Billing"), 
        help_text=_("Customer will be charged the regular product price on a periodic basis."), 
        default=False)
    recurring_times = models.IntegerField(_("Recurring Times"), 
        help_text=_("Number of payments which will occur at the regular rate.  (optional)"), 
        null=True, blank=True)
    expire_length = models.IntegerField(_("Duration"), 
        help_text=_("Length of each billing cycle"), 
        null=True, blank=True)
    SUBSCRIPTION_UNITS = (
        ('DAY', _('Days')),
        ('MONTH', _('Months'))
    )
    expire_unit = models.CharField(_("Expire Unit"), max_length=5, 
        choices=SUBSCRIPTION_UNITS, default="DAY", null=False)
    SHIPPING_CHOICES = (
        ('0', _('No Shipping Charges')),
        ('1', _('Pay Shipping Once')),
        ('2', _('Pay Shipping Each Billing Cycle')),
    )

# --------------------
# Helper methods
# --------------------

def _decrypt_code(code):
    """Decrypt code encrypted by _encrypt_code"""
    secret_key = settings.SECRET_KEY
    encryption_object = Blowfish.new(secret_key)
    # strip padding from decrypted credit card number
    return encryption_object.decrypt(base64.b64decode(code)).rstrip('X')

def _encrypt_code(code):
    """Quick encrypter for CC codes or code fragments"""
    secret_key = settings.SECRET_KEY
    encryption_object = Blowfish.new(secret_key)
    # block cipher length must be a multiple of 8
    padding = ''
    if (len(code) % 8) <> 0:
        padding = 'X' * (8 - (len(code) % 8))
    return base64.b64encode(encryption_object.encrypt(code + padding))
