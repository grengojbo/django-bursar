from django.views.decorators.cache import never_cache
from bursar.models import Payment
from bursar.gateway.paypal_gateway import processor
import logging
import urllib2

log = logging.getLogger('bursar.gateway.paypal_gateway')

@never_cache
def ipn(request, settings=None):
    """PayPal IPN (Instant Payment Notification)
    Cornfirms that payment has been completed and marks invoice as paid.
    Adapted from IPN cgi script provided at http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/456361"""
    
    if not settings:
        raise GatewayError('Paypal IPN needs settings, please put into your urls.')
    
    live = settings['LIVE']
    if live:
        log.debug("Live IPN on %s", settings['KEY'])
        url = settings['POST_URL']
        account = settings['BUSINESS']
    else:
        log.debug("Test IPN on %s", payment_module.KEY.value)
        url = settings['POST_TEST_URL']
        account = settings['BUSINESS_TEST']

    PP_URL = url

    try:
        data = request.POST
        log.debug("PayPal IPN data: " + repr(data))
        if not confirm_ipn_data(data, PP_URL):
            return HttpResponse()

        if not 'payment_status' in data or not data['payment_status'] == "Completed":
            # We want to respond to anything that isn't a payment - but we won't insert into our database.
             log.info("Ignoring IPN data for non-completed payment.")
             return HttpResponse()

        try:
            invoice = data['invoice']
        except:
            invoice = data['item_number']

        gross = data['mc_gross']
        txn_id = data['txn_id']

        # skip if we've already handled this one
        if Payment.objects.filter(transaction_id=txn_id).count() > 0:
            log.warn('IPN received for transaction #%s, already processed', txn_id)
            return HttpResponse()
        else:
            # TODO: deal with retry - txn_id is going to have a suffix
            purchase = Purchase.objects.get(transaction_id=txn_id)
            processor = processor.PaymentProcessor(settings=settings)
            payment = processor.record_payment(
                amount = gross,
                transaction_id = txn_id,
                purchase = purchase
                )
            
            if 'memo' in data:
                payment.add_note(_('---Comment via Paypal IPN---') + u'\n' + data['memo'])
                log.debug("Saved order notes from Paypal: %s" % data['memo'])
            
            # order = Order.objects.get(pk=invoice)
            #             
            #             order.add_status(status='New', notes=_("Paid through PayPal."))
            
            #TODO: verify - is this right? not sure if I should be settings them to "completed"
            for item in purchase.recurring_lineitems:
                if not item.completed:
                    item.completed = True
                    item.save()

    except:
        log.exception(''.join(format_exception(*exc_info())))

    return HttpResponse()

def confirm_ipn_data(data, PP_URL):
    # data is the form data that was submitted to the IPN URL.

    newparams = {}
    for key in data.keys():
        newparams[key] = data[key]

    newparams['cmd'] = "_notify-validate"
    params = urlencode(newparams)

    req = urllib2.Request(PP_URL)
    req.add_header("Content-type", "application/x-www-form-urlencoded")
    fo = urllib2.urlopen(req, params)

    ret = fo.read()
    if ret == "VERIFIED":
        log.info("PayPal IPN data verification was successful.")
    else:
        log.info("PayPal IPN data verification failed.")
        log.debug("HTTP code %s, response text: '%s'" % (fo.code, ret))
        return False

    return True
