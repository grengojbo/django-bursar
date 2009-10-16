from bursar.fields import CurrencyField
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from satchmo_utils.admin import AutocompleteAdmin
from bursar.models import Authorization, CreditCardDetail, Payment, PaymentFailure, \
                        PaymentNote, PaymentPending, Purchase, LineItem, \
                        RecurringLineItem, Payment

#
class Authorization_Inline(admin.TabularInline):
    model = Authorization
    extra = 0

class CreditCardDetail_Inline(admin.TabularInline):
    model = CreditCardDetail
    extra = 0

class LineItem_Inline(admin.TabularInline):
    model = LineItem
    extra = 1
        
class Payment_Inline(admin.TabularInline):
    model = Payment
    extra = 1

class PaymentNote_Inline(admin.TabularInline):
    model = PaymentNote
    extra = 1

class PaymentFailure_Inline(admin.TabularInline):
    model = PaymentFailure
    extra = 0

class PaymentPending_Inline(admin.TabularInline):
    model = PaymentPending
    extra = 0

# class RecurringLineItem_Inline(admin.TabularInline):
#     model = RecurringLineItem
#     extra = 1

class PurchaseOptions(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('site', 'orderno')}),
        (_('Purchaser'), {'fields': ('first_name', 'last_name', 'email', 'phone', )}), 
        (_('Shipping Address'), 
            {'classes': ('collapse',), 
             'fields': ('ship_street1', 'ship_street2', 'ship_city', 'ship_state', 'ship_postal_code', 'ship_country')}),
        (_('Billing Address'), 
            {'classes': ('collapse',),
             'fields': ('bill_street1', 'bill_street2', 'bill_city', 'bill_state', 'bill_postal_code', 'bill_country')}),
        (_('Totals'), 
            {'fields': ('sub_total', 'shipping', 'tax', 'total', 'time_stamp')})
    )
    list_display = ('id', 'first_name', 'last_name', 'time_stamp', 'total', 'authorized_remaining', 'remaining')
    list_filter = ['time_stamp', 'last_name']
    date_hierarchy = 'time_stamp' 
    list_filter = ['time_stamp'] 
    inlines = [Payment_Inline, PaymentPending_Inline,  PaymentFailure_Inline, LineItem_Inline] #, RecurringLineItem_Inline]

# class OrderItemOptions(admin.ModelAdmin):
#     inlines = [OrderItemDetail_Inline]
# 
class PaymentOptions(AutocompleteAdmin):
    list_filter = ['method']
    list_display = ['id', 'transaction_id', 'success', 'method', 'amount', 'time_stamp']
    fieldsets = (
        (None, {'fields': ('purchase','success', 'method', 'amount',  'transaction_id', 'reason_code', 'time_stamp', 'details')}), )
    raw_id_fields = ['purchase']
    inlines = [CreditCardDetail_Inline, PaymentNote_Inline]
    

# class OrderAuthorizationOptions(OrderPaymentOptions):
#     list_display = ['id', 'order', 'capture', 'payment', 'amount_total', 'complete', 'time_stamp']
#     fieldsets = (
#         (None, {'fields': ('order', 'capture', 'payment', 'amount', 'transaction_id', 'complete', 'time_stamp')}), )

admin.site.register(Purchase, PurchaseOptions)
admin.site.register(Payment, PaymentOptions)
import logging
log = logging.getLogger('bursar.admin')
log.debug('registered admin for Bursar')
