from bursar.fields import CurrencyField
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from bursar.models import Authorization, CreditCardDetail, Payment, PaymentFailure, \
                        PaymentNote, PaymentPending, Purchase, LineItem, \
                        RecurringLineItem, Payment


class AutocompleteAdmin(admin.ModelAdmin):
    """Admin class for models using the autocomplete feature.

    There are two additional fields:
       - related_search_fields: defines fields of managed model that
         have to be represented by autocomplete input, together with
         a list of target model fields that have to be searched for
         input string,
       - related_string_functions: contains optional functions which
         take target model instance as only argument and return string
         representation. By default __unicode__() method of target
         object is used.
    """

    related_search_fields = {}
    related_string_functions = {}

    def __call__(self, request, url):
        # This is deprecated interface and will be dropped in Django 1.3.
        # Since the version 1.1, Django uses get_urls() method below.
        if url is None:
            pass
        elif url == 'search':
            return self.search(request)
        return super(AutocompleteAdmin, self).__call__(request, url)

    def get_urls(self):
        from django.conf.urls.defaults import url
        patterns = super(AutocompleteAdmin, self).get_urls()
        info = self.admin_site.name, self.model._meta.app_label, self.model._meta.module_name
        patterns.insert(
                -1,     # insert just before (.+) rule (see django.contrib.admin.options.ModelAdmin.get_urls)
                url(
                    r'^search/$',
                    self.search,
                    name='%sadmin_%s_%s_search' % info
                    )
                )
        return patterns

    def search(self, request):
        """
        Searches in the fields of the given related model and returns the
        result as a simple string to be used by the jQuery Autocomplete plugin
        """
        query = request.GET.get('q', None)
        app_label = request.GET.get('app_label', None)
        model_name = request.GET.get('model_name', None)
        search_fields = request.GET.get('search_fields', None)
        try:
            to_string_function = self.related_string_functions[model_name]
        except KeyError:
            to_string_function = lambda x: x.__unicode__()

        if search_fields and app_label and model_name and query:
            def construct_search(field_name):
                # use different lookup methods depending on the notation
                if field_name.startswith('^'):
                    return "%s__istartswith" % field_name[1:]
                elif field_name.startswith('='):
                    return "%s__iexact" % field_name[1:]
                elif field_name.startswith('@'):
                    return "%s__search" % field_name[1:]
                else:
                    return "%s__icontains" % field_name

            model = models.get_model(app_label, model_name)
            qs = model._default_manager.all()
            for bit in query.split():
                or_queries = [models.Q(**{construct_search(
                    smart_str(field_name)): smart_str(bit)})
                        for field_name in search_fields.split(',')]
                other_qs = QuerySet(model)
                other_qs.dup_select_related(qs)
                other_qs = other_qs.filter(reduce(operator.or_, or_queries))
                qs = qs & other_qs
            data = ''.join([u'%s|%s\n' % (to_string_function(f), f.pk) for f in qs])
            return HttpResponse(data)
        return HttpResponseNotFound()

    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Overrides the default widget for Foreignkey fields if they are
        specified in the related_search_fields class attribute.
        """
        if isinstance(db_field, models.ForeignKey) and \
                db_field.name in self.related_search_fields:
            kwargs['widget'] = ForeignKeySearchInput(
                    db_field.rel,
                    self.related_search_fields[db_field.name],
                    self.related_string_functions.get(db_field.name)
                    )
        field = super(AutocompleteAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        return field


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


class PaymentOptions(AutocompleteAdmin):
    list_filter = ['method']
    list_display = ['id', 'transaction_id', 'success', 'method', 'amount', 'time_stamp']
    fieldsets = (
        (None, {'fields': ('purchase','success', 'method', 'amount',  'transaction_id', 'reason_code', 'time_stamp', 'details')}), )
    raw_id_fields = ['purchase']
    inlines = [CreditCardDetail_Inline, PaymentNote_Inline]


admin.site.register(Purchase, PurchaseOptions)
admin.site.register(Payment, PaymentOptions)
