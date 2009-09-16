from bursar.models import CreditCardDetail
from django.contrib import admin

class CreditCardDetail_Inline(admin.StackedInline):
    model = CreditCardDetail
    extra = 1

# class PaymentOptionOptions(admin.ModelAdmin):
#     list_display = ['optionName','description','active']
#     ordering = ['sortOrder']
# 
# admin.site.register(PaymentOption, PaymentOptionOptions)

