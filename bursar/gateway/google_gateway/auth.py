from django.http import HttpResponse
from livesettings import config_get_group
from payment.config import gateway_live

def auth_required(request):
    """
    Sends an authentication required response
    """
    response = HttpResponse(('Authorization Required'), mimetype="text/plain")
    response['WWW-Authenticate'] = 'Basic'
    response.status_code = 401
    return response

def get_cred():
    gateway_settings = config_get_group('PAYMENT_GOOGLE')
    live = gateway_live(gateway_settings)
    # get key and value
    if live:
        merchant_id = gateway_settings.MERCHANT_ID.value
        merchant_key = gateway_settings.MERCHANT_KEY.value
    else:
        merchant_id = gateway_settings.MERCHANT_TEST_ID.value
        merchant_key = gateway_settings.MERCHANT_TEST_KEY.value
    
    return (merchant_id, merchant_key)

def get_url():
    """
    Returns the urls needed
    """
    (merchant_id, merchant_key) = get_cred()
    gateway_settings = config_get_group('PAYMENT_GOOGLE')
    live = gateway_live(gateway_settings)
    if live:
        url_template = gateway_settings.POST_URL.value
    else:
        url_template = gateway_settings.POST_TEST_URL.value
    post_url = url_template % {'MERCHANT_ID' : merchant_id}
    return post_url

def do_auth(request):
    try:
        (merchant_id, merchant_key) = get_cred()
        # now get the http auth values
        http_auth = request.META['HTTP_AUTHORIZATION']
        (authmeth, auth) = http_auth.split(' ', 1)
        (username, password) = auth.strip().decode('base64').split(':', 1)
        if username != merchant_id:
            raise Exception()
        if password != merchant_key:
            raise  Exception()
        # passed auth
    except:
        return auth_required(request)