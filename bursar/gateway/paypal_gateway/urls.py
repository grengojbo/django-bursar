from bursar.bursar_settings import get_bursar_setting
from django.conf.urls.defaults import *
from django.conf import settings

def make_urlpatterns(gateway_settings, ssl=False, ipn_test=False):
    urlpatterns = patterns('bursar.gateway.paypal_gateway.views',
        (r'^ipn/$', 'ipn', 
            {'SSL': ssl, 'settings' : gateway_settings},
            'PAYPAL_GATEWAY_ipn'),
    )

    if ipn_test:
        import logging
        log = logging.getLogger('bursar.gateway.paypal_gateway')
        log.warn('IPN Test url is active')
        urlpatterns += patterns('bursar.gateway.paypal_gateway.views',
            (r'^ipn_test/$', 'ipn_test', 
                {'SSL': ssl, 'settings' : gateway_settings},
                'PAYPAL_GATEWAY_ipn_test'),
        )
    return urlpatterns

# by default, look up from Bursar settings.
if settings.DEBUG:
    key = 'PAYPAL_TEST'
else:
    key = 'PAYPAL'

paypal_settings = get_bursar_setting(key, default_value={})
ssl = paypal_settings.get('SSL', False)
ipn_test = paypal_settings.get('IPN_TEST')
urlpatterns = make_urlpatterns(paypal_settings, ssl=ssl, ipn_test=ipn_test)
