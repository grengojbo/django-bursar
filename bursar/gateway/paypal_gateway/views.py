from bursar.errors import GatewayError
from bursar.gateway.paypal_gateway import processor
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.cache import never_cache
import logging

log = logging.getLogger('bursar.gateway.paypal_gateway')

@never_cache
def ipn(request, settings=None):
    """PayPal IPN (Instant Payment Notification)
    Confirms that payment has been completed and marks invoice as paid.
    Adapted from IPN cgi script provided at http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/456361"""
    
    if not settings:
        raise GatewayError('Paypal IPN needs settings, please put into your urls.')
    
    gateway = processor.PaymentProcessor(settings=settings)

    sane = True
    
    if not request.method == "POST":
        log.warn("IPN request - no post data, ignoring.")
        sane = False

    else:
        data = request.POST.copy()
        if not gateway.confirm_ipn_data(data):
            sane = False
            
    if sane:
        status = data.get('payment_status', 'unknown')
        if status != "Completed":
            # We want to respond to anything that isn't a payment - but we won't insert into our database.
             log.info("Ignoring IPN data for non-completed payment. Status is '%s'", status)
             sane = False

    if sane:
        invoice = data.get('invoice', '')
        if not invoice:
            invoice = data.get('item_number', '')
        
        if not invoice:
            log.info("No invoice # in data, aborting IPN")
            sane = False

    if sane:
        gross = data['mc_gross']
        txn_id = data['txn_id']
        note = data.get('memo', '')
        gateway.accept_ipn(invoice, gross, txn_id, note)

    return HttpResponse()
    
@never_cache
def ipn_test(request, settings=None):
    """Manually triggers an IPN result"""
    from bursar.gateway.paypal_gateway.forms import IpnTestForm

    if not settings:
        raise GatewayError('Paypal IPN needs settings, please put into your urls.')

    gateway = processor.PaymentProcessor(settings=settings)

    if request.method == "POST":
        data = request.POST.copy()
        form = IpnTestForm(data)
        if form.is_valid():
            log.debug('Doing an IPN test on %s', data)
            data = form.cleaned_data
            invoice = data['invoice']
            gross = data['amount']
            transaction_id = data['transaction']
            note = data['note']
            gateway.accept_ipn(invoice, gross, transaction_id, note)
    else:
        form = IpnTestForm()
        
    ctx = RequestContext(request, { 
        'form' : form,
    })

    return render_to_response('bursar/gateway/paypal_gateway/ipn_test.html', ctx)

